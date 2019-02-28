#include <avr/sleep.h>
#include <avr/wdt.h>
#define HEART_CYCLE 10800     //24小时唤醒
//String ALARM = "00100";     //报警通知
String OPEN_DONE = "00201"; //开锁成功反馈
String OPEN_FAIL = "00202"; //开锁失败反馈
//String CLOSE_DONE = "00211";//闭锁指令成功状态
//String CLOSE_FAIL = "00212";//闭锁指令失败状态
//String BAT = "00300";       //电量通知
String HEART = "00505";     //心跳通知
//String ID = "0058658871";   //设备ID
//String ID = "0040046415";
//String ID = "2018050204";
//String ID = "2018040401";
String ID = "2018050201";
//String ID = "2018073109";
//String ID = "2018073109";
//String ID = "0000012345";
//String ID = "2018053101";
//String ID = "2018073102";
//String ID = "2018061901";

String SEND_CONTENT = "";
String SendData = "";
String ReturnData = "";
String Bat_Vol = "";
String Battery = "";
String CONTENT_1 = "";
String CONTENT_2 = "";


const int Battary_Voltage_Pin = 0;
const int Alarm_Pin = 2;      //磁感
const int Button_Pin = 3;     //按钮
const int self_reset_pin = 4;
const int Power_Module_Pin = 5;

const int Lock_State = 8;     //微动开关
const int Lock_Power = 9; //锁子上电
const int Reset_SIM7000C_Pin = 10;
const int Network_State_Pin = 11;
const int Lock_Control_Pin = 12;  //开锁
const int NB_Pin = 13;

volatile int sleep_count = 0;
volatile byte ISR_Flag = 0;
long int current_time = 0;

int main_state = 0;
int alarm_flag;
int alarm_state = 0;
int Battery_Voltage = 0;
int send_msg_counter = 0;
int opne_flag = 0;
int battery_counter = 0;
int connect_to_net_counter = 0;

typedef enum _FSM_GSM_TO_NET_STATE {
  Send_AT = 0,            //检查串口
  Send_AT_CNMP = 1,       //切换到LTE网络
  Send_AT_CMNB = 2,       //切换到NBIOT  
  Send_AT_NBSC = 3,       //打开扰码，需要和基站确认
  Send_AT_COPS = 4,       //查询注册网络
  Send_AT_CGATT = 5,      //查询附着和分离GPRS业务
  Send_AT_CPSI = 6,       //查询GSM信号 
//  Send_AT_CSTT = 7,
  Send_AT_CSTT_CMNET = 7, //启动任务并设置接入点APN、用户名、密码
  Send_AT_CIICR = 8,      //打开无线连接
  Send_AT_CIFSR = 9,      //获取本地IP地址
} FSM_GSM_TO_NET_STATE;
FSM_GSM_TO_NET_STATE sim7000_state = Send_AT;

typedef enum _FSM_GSM_SEND_DATA_STATE {
  GSM_Connect_To_Server = 0,
  GSM_AT_Send = 1,
  Read_AD_Data = 2,
  GSM_Send_Data_To_Server = 3,
  Restart_Module = 4,
  Display_Data = 5,
} FSM_GSM_SEND_DATA_STATE;
FSM_GSM_SEND_DATA_STATE send_state = GSM_Connect_To_Server;

int send_at_counter;
int send_cpos_counter = 0;
int send_cipsend_counter = 0;
int send_counter = 0;
int get_counter;
int lock_open_state = 0;
int connect_state = 0;
int send_data_state = 0;
int Open_Close_Flag;
int connect_net_counter = 0;

boolean Connect_To_Net() {

  switch (sim7000_state) {
    case Send_AT:
      Serial.println("AT");
      delay(50);
      ++send_at_counter;
      if (Serial.find("OK")) {
        sim7000_state = Send_AT_CNMP;
        return false;
      }
      else {
        Serial.println(send_at_counter);
        if (send_at_counter == 50) {
          send_at_counter = 0;
          Serial.println("AT+CPOWD=1");//Restart off module
          delay(2000);
        }
        sim7000_state = Send_AT;
        return false;
      }
      break;

    case Send_AT_CNMP:
      Serial.println("AT+CNMP=38");
      delay(100);
      if (Serial.find("OK")) {
//        Serial.println("Send AT+CNMP=38 command OK.");
        sim7000_state = Send_AT_CMNB;
        return false;
      }
      else {
//        Serial.println("Send AT+CNMP=38 command again.");
        sim7000_state = Send_AT_CNMP;
        return false;
      }
      break;

    case Send_AT_CMNB:
      Serial.println("AT+CMNB=2");
      delay(100);
      if (Serial.find("OK")) {
//        Serial.println("Send AT+CMNB=2 command OK.");
//        Serial.println("Set as NB mode done.");
        sim7000_state = Send_AT_NBSC;
        return false;
      }
      else {
//        Serial.println("Send AT+CMNB=2 command again.");
        sim7000_state = Send_AT_CMNB;
        return false;
      }
      break;

    case Send_AT_NBSC:
      Serial.println("AT+NBSC=1");
      delay(100);
      if (Serial.find("OK")) {
//        Serial.println("Send AT+NBSC=1 command OK.");
        sim7000_state = Send_AT_COPS;
        return false;
      }
      else {
//        Serial.println("Send AT+NBSC=1 command again.");
        sim7000_state = Send_AT_NBSC;
        return false;
      }
      break;

    case Send_AT_COPS:
      Serial.println("AT+COPS?");//The module return "CMCC" means module have connect to GSM network
      ++send_cpos_counter;
      delay(100);
      if (Serial.find("9")) {
//        Serial.println("Send AT+COPS? command OK.");
        sim7000_state = Send_AT_CGATT;
        return false;
      }
      else {
//        Serial.println("Send AT+COPS? command again.");
        if (send_cpos_counter == 100) {
          send_at_counter = 0;
//          Serial.println("Force Reset Module!");
          Serial.println("AT+CPOWD=1");//Restart module
          delay(1000);
          digitalWrite(self_reset_pin, LOW);
          delay(2000);
        }
      }
      break;

    case Send_AT_CGATT:
      Serial.println("AT+CGATT?");//attach to GSM network
      delay(100);
      if (Serial.find("CGATT: 1")) {
//        Serial.println("Send AT+CGATT? command OK.");
        sim7000_state = Send_AT_CPSI;
        return false;
      }
      else {
//        Serial.println("Send AT+CGATT? command again.");
        sim7000_state = Send_AT_CGATT;
        return false;
      }
      break;

    case Send_AT_CPSI:
      Serial.println("AT+CPSI?");//see the network information and module status
      delay(100);
      if (Serial.find("Online")) {
//        Serial.println("Send AT+CPSI? command OK.");
        sim7000_state = Send_AT_CSTT_CMNET;
        return false;
      }
      else {
//        Serial.println("Send AT+CPSI? command again.");
        sim7000_state = Send_AT_CPSI;
        return false;
      }
      break;

    case Send_AT_CSTT_CMNET:
      Serial.println("AT+CSTT=\"CMNBIOT\"");//电信的话将CMNBIOT改为CTNB
      delay(100);
      if (Serial.find("OK")) {
//        Serial.println("AT+CSTT=\"CMNBIOT\" command OK.");
        sim7000_state = Send_AT_CIICR;
        return false;
      }
      else {
        Serial.println("AT+CIPSTART=\"TCP\",\"47.94.128.180\",1001");
        if (Serial.find("CONNECT OK")) {
//          Serial.println("Already connected to Server.");
          connect_state = 1; //Entery send data ststus 2
          return true;
          break;
        }
        else {
          Serial.println("AT+CPOWD=1");
          delay(8000);
          delay(8000);
//          Serial.println("Restart SIM7000C module");
          sim7000_state = Send_AT;
          return false;
        }
      }
      break;

    case Send_AT_CIICR:
      Serial.println("AT+CIICR");
      delay(100);
      if (Serial.find("OK")) {
//        Serial.println("Send AT+CIICR command OK.");
        sim7000_state = Send_AT_CIFSR;
        return false;
        break;
      }
      else {
        Serial.println("AT+CIPSTART=\"TCP\",\"47.94.128.180\",1001");//connect to manhole cover server
        if (Serial.find("CONNECT OK")) {
//          Serial.println("Already connected to Server.");
          connect_state = 1; //Entery send data ststus 1
          return true;
          break;
        }
        else {
          Serial.println("AT+CPOWD=1");//or use nRST pin to reset module
          delay(8000);
          delay(8000);
//          Serial.println("Restart SIM7000C module");
          sim7000_state = Send_AT;
          return false;
        }
      }
      break;
    case Send_AT_CIFSR:
      Serial.println("AT+CIFSR");
      sim7000_state = Send_AT;
      return true;

  }
}

void setup() {

  setup_watchdog(9);
  ACSR |= _BV(ACD); //OFF ACD
  ADCSRA = 0; //OFF ADC
  Serial.begin(115200);
 
  digitalWrite(self_reset_pin, HIGH);
  pinMode(self_reset_pin, OUTPUT);

  pinMode(Network_State_Pin, OUTPUT);
  
  pinMode(Lock_Control_Pin, OUTPUT);
  digitalWrite(Lock_Control_Pin, LOW);

  pinMode(NB_Pin, OUTPUT);
  digitalWrite(NB_Pin, LOW);

  pinMode(Power_Module_Pin, OUTPUT);
  digitalWrite(Power_Module_Pin, HIGH);

  pinMode(Reset_SIM7000C_Pin, OUTPUT);
  digitalWrite(Reset_SIM7000C_Pin, HIGH);


  pinMode(Alarm_Pin, INPUT_PULLUP);
  pinMode(Button_Pin, INPUT_PULLUP);
  
  pinMode(Lock_State, INPUT_PULLUP);
//  pinMode(Lock_Power, OUTPUT);
//  digitalWrite(Lock_Power,HIGH);
  
  digitalWrite(Network_State_Pin,HIGH);
  delay(5000);
  digitalWrite(Network_State_Pin,LOW);
  digitalWrite(NB_Pin, HIGH);
//  digitalWrite(Power_Module_Pin, HIGH);

/*  digitalWrite(Reset_SIM7000C_Pin, LOW);
  Serial.println("Restart the SIM7000C module.");
  delay(5000);
  digitalWrite(Reset_SIM7000C_Pin, HIGH);*/

  Serial.println("AT+CIPCLOSE=1");//Close Server connection
  
  attachInterrupt(0, wakeISR1, CHANGE);
  attachInterrupt(1, wakeISR2, LOW);
 
}

void loop(){
  
  sleep_disable();
  switch (main_state) {

    case 0:
    
      if (Connect_To_Net() == true) {
        main_state = 1;
      }
      else{
        ++connect_to_net_counter;
        if(connect_to_net_counter >= 300){
          main_state = 3;
        }
        else{
          main_state = 0;
        }
      }
    break;

    case 1:
   
      ++battery_counter;
      if (Get_Battary_Voltage() == true) {
        main_state = 2;
      }
      else {
        Serial.println(battery_counter);
        if (battery_counter >= 100)
          main_state = 2;
        else
          main_state = 1;
      }
      break;

    case 2:
     
      Send_Bat_Voltage_Open_Lock();
//      Serial.println(send_msg_counter);
      Get_Open_Cmd_From_Server_2();
      if (send_msg_counter >= 200) {
//        Serial.println("AT+CIPCLOSE");//Close Server connection
        Serial.println("AT+CIPCLOSE=1");//Close Server connection
        delay(2000);
//        digitalWrite(Lock_Power,LOW);
        digitalWrite(Network_State_Pin,LOW);//turn off network led
        digitalWrite(Power_Module_Pin, LOW);
        digitalWrite(NB_Pin, LOW);
        main_state = 3;
      }
      else {
        ++send_msg_counter;
        main_state = 2;
      }
      break;

    case 3:
      digitalWrite(NB_Pin, LOW);
      digitalWrite(Power_Module_Pin, LOW);
      if (sleep_count >= HEART_CYCLE) {
        sleep_count = 0;
        Serial.println("8 Hours SelfReset!");
        digitalWrite(self_reset_pin, LOW);
        delay(2000);
      }
      else {
        Sleep_avr();
        main_state = 3;
      }
      break;
  }
}
void setup_watchdog(int ii) {

  byte bb;
  if (ii > 9 ) ii = 9;
  bb = ii & 7;
  if (ii > 7) bb |= (1 << 5);
  bb |= (1 << WDCE);

  MCUSR &= ~(1 << WDRF);
  // start timed sequence
  WDTCSR |= (1 << WDCE) | (1 << WDE);
  // set new watchdog timeout value
  WDTCSR = bb;
  WDTCSR |= _BV(WDIE);
}

void Sleep_avr() {
  set_sleep_mode(SLEEP_MODE_PWR_DOWN); // sleep mode is set here
  sleep_enable();
  sleep_mode();                        // System sleeps here
  sleep_disable();
}

//WDT interrupt
ISR(WDT_vect) {
  ++sleep_count;
}
void wakeISR1() {
  Serial.println("Interrupt 1 SelfReset!");
  digitalWrite(self_reset_pin, LOW);
}
void wakeISR2() {
  Serial.println("Interrupt 2 SelfReset!");
  digitalWrite(self_reset_pin, LOW);
}

void Send_Bat_Voltage_Open_Lock() {
  //int send_counter = 0;
  switch (connect_state) {
    case 0:
//      mySerial.println("AT+CIPSTART=\"TCP\",\"47.94.128.180\",1001");//Connect to  manhole cover server
      Serial.println("AT+CIPSTART=\"TCP\",\"47.94.128.180\",1001");
      delay(20);
//      Serial.print("AT+CIPSTART send times: ");
//      Serial.println(send_counter);
      if (Serial.find("CONNECT")) {
        connect_state = 1;
      }
      else {
        ++send_counter;
        if (send_counter >= 30) { //先改为连接30次失败后重启
//          send_counter = 0;
          connect_state = 8;
        }
        else
          connect_state = 0;
      }
      break;

    case 1:
      Get_Open_Cmd_From_Server_2();
      //      digitalWrite(Network_State_Pin,LOW);
      Serial.println("AT+CIPSEND");
      ++send_cipsend_counter;
      delay(100);
//      Serial.print("AT+CIPSEND times:");
//      Serial.println(send_cipsend_counter);

      if (Serial.find("ERROR"))
        connect_state = 8;//这里有些问题需要注意
      else
        connect_state = 2;
      break;

    case 2:
      Get_Open_Cmd_From_Server_2();

      if (digitalRead(Alarm_Pin) == LOW)
        CONTENT_1 = '1';//open
      else
        CONTENT_1 = '0';//close

      if (digitalRead(Lock_State) == LOW)
        CONTENT_2 = '0'; //open
      else
        CONTENT_2 = '1';//close

      Get_Open_Cmd_From_Server_2();
      connect_state = 4;
    break;

    case 4:
      Get_Open_Cmd_From_Server_2();
      Send_Data_to_Server(ID, HEART, CONTENT_1, CONTENT_2, Battery); //send status to server build the connection with server

      if (Get_Heart_Data_From_Server_2() == true) { //wait server feedback
          digitalWrite(Network_State_Pin,HIGH);//turn on network led
          connect_state = 5;
          Serial.println("Send Heart Done!");
      }
      else
        connect_state = 1;

      break;

    case 5:
      if (Get_Open_Cmd_From_Server() == true) { //get server command
        connect_state = 6;
      }
      else
        connect_state = 1;
      break;

    case 6:
      Serial.println("AT+CIPSEND");
      delay(100);
      if (Serial.find("ERROR"))
        connect_state = 8;
      else
        connect_state = 7;
      break;

    case 7:
      if (Open_Close_Flag == 1) {
        Send_Data_to_Server(ID, OPEN_DONE, CONTENT_1, CONTENT_2, Battery);
//        Serial.println("Feedback OPE.");
      }
      /*  if(Open_Close_Flag ==2){
          Send_Data_to_Server(ID,CLOSE_DONE,CONTENT_1,SEND_CONTENT);
          Serial.println("Feedback CLO.");
        }*/
      connect_state = 1;
      break;


    case 8:
//      Serial.println("SelfReset!");
      digitalWrite(self_reset_pin, LOW);
      delay(2000);
      //      digitalWrite(self_reset_pin,HIGH);
      break;
  }
}

boolean Get_Heart_Data_From_Server() { //get server back data
  char terminator = 'e';
  long int get_upload_timer;
  get_upload_timer = millis();
  //  Serial.print("get_upload_timer:");
  //  Serial.println(get_upload_timer);

  while (!CheckTimer(get_upload_timer, 10)) { //wait 20 seconds
    if (Serial.available()) {
      if (Serial.find("00505")) {
//        ReturnData = mySerial.readStringUntil(terminator);
//        ReturnData = '0' + ReturnData + 'e';
//        Serial.println(ReturnData);//at here the program stop.
        Serial.println("Get Heart Done!");
        return true;
      }
    }
  }
  return false;
  ReturnData = "";
}

boolean Get_Heart_Data_From_Server_2() { //get server back data
  
  for(int i;i<2000;i++){
    if (Serial.find("00505")) {
      Serial.println("Get Heart Done!");
      return true;
      }
    else 
      return false;
  }
  ReturnData = "";
}

boolean Get_Open_Cmd_From_Server() {
  
//  Serial.println("Wait Command...");
//  while (!CheckTimer(cmd_upload_timer, 10)) { //wait 20 seconds to receive cmd
  for(int i=0;i<=1500;i++){
    if (Serial.available()) {
      if (Serial.find("00200")) {
        Open_Lock();
        Serial.println("AT+CIPSEND");
        delay(100);
        Send_Data_to_Server(ID, OPEN_DONE, CONTENT_1, CONTENT_2, Battery);
        return true; //exit CheckTimer function
      }
    }
  }
    return false;
//  }
}

void Get_Open_Cmd_From_Server_2() {
//  Serial.println("Wait Command...");
  for(int i=0;i<=1500;i++){
    if (Serial.available()) {
      if (Serial.find("00200")) {
        Open_Lock();
//        Serial.println("Get Open Command Done!");
        Serial.println("AT+CIPSEND");
        delay(100);
        Send_Data_to_Server(ID, OPEN_DONE, CONTENT_1, CONTENT_2, Battery);
//        Serial.println("Feedback OPE.");
        connect_state = 1;
      }
    }
  }
}

boolean CheckTimer(unsigned long timer, unsigned long period) {
  current_time = millis();
  if (current_time >= timer) {
    if ((current_time - timer) > (period * 1000)) { //30mins clean
      return true;
    }
  } else if (((4294967295 - timer) + current_time) > (period * 1000)) { //30mins clean
    return true;
  }

  return false;
}

void Send_Data_to_Server(String id, String command, String cover_status, String lock_status, String data) {

  Serial.print(id);
  Serial.print(command);
  Serial.print(cover_status);
  Serial.print(lock_status);
  Serial.print("0000000000");
  Serial.println(data);
  Serial.println();
  Serial.write(0x1A);
  
//  Serial.print(id);
//  Serial.print(command);
//  Serial.print(cover_status);
//  Serial.print(lock_status);
//  Serial.print("0000000000");
//  Serial.println(data);
//  Serial.println();



}


boolean Get_Battary_Voltage() {
  char terminator = 'K';
  Serial.println("AT+CBC");
  delay(100);
  if (Serial.available() > 0)
    Bat_Vol = Serial.readStringUntil(terminator);

  Bat_Vol = Bat_Vol.substring(21, 25);
  Battery_Voltage = Bat_Vol.toInt();
  Bat_Vol = "";
  if (Battery_Voltage > 100) {
    //       Serial.println(Battery_Voltage);
    Battery = Battery_Voltage;
    return true;
  }
  else
    return false;
}


void Open_Lock() {

  digitalWrite(Lock_Control_Pin, HIGH);
  while (!(digitalRead(Lock_State) == LOW)) {
    delay(500);
  }
  digitalWrite(Lock_Control_Pin, LOW);
  Open_Close_Flag = 1;
}
