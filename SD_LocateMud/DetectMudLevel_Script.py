import time
from openpyxl import Workbook  # 写入excel用的库
import queue

class PsTrackers( list ):
    """
    定义16个光敏追踪器的类。
    """
    def __init__(self, timewindow):
        """
        function: 初始化16个光敏追踪器，即(timewindow*6) * 16的空table, 可视为是16个队列组成的table。
        :param timewindow: 追踪多长时间的光敏值，单位为分钟，至少1分钟。
        """

        #  Sentinel.
        assert timewindow >= 1, "光敏追踪器时间窗至少为1分钟。"

        list.__init__([])  # 继承list类。
        m = timewindow * 6 + 1  # 光敏追踪器的行数, 加1是由于队列的结构。
        n = 16
        self.trackers = [[[] for i in range(n)] for j in range(m)]  # 追踪器初值。
        self.brokelist = [False for i in range(16)]  #  损坏光敏列表。
        self.rows = m
        self.head = 0  # 光敏追踪器的head。
        self.tail = 0  # 光敏追踪器的tail。
        self.mean = 0  # 追踪器的均值。
        self.stddev = 0  #  追踪器的标准差。


    def reset(self):
        """
        function: 清除追踪器内的所有数据。
        """
        n = 16
        m = self.rows
        self.trackers = [[[] for i in range(n)] for j in range(m)]  # 追踪器初值。
        self.brokelist = [False for i in range(16)]  #  损坏光敏列表。
        self.head = 0  # 光敏追踪器的head。
        self.tail = 0  # 光敏追踪器的tail。
        self.mean = 0  # 追踪器的均值。
        self.stddev = 0  #  追踪器的标准差。


    def isempty( self ):
        """
        function:判断当前队列是否为空。
        :return: True if it is empty, False otherwise.
        """
        if self.tail == self.head:
            return True
        else:
            return False


    def isfull( self ):
        """
        function:判断当前队列是否已满。
        :return: True if it is full, False otherwise.
        """
        if (self.tail + 1 == self.head) or (self.head == 0 and self.tail == self.rows - 1):
            return True
        else:
            return False


    def dequeue( self ):
        """
        function:从队列table的head弹出一行元素。
        :return: 弹出的一行16个元素值。
        """

        #  取出参数。
        trackers = self.trackers
        head = self.head
        tail = self.tail
        rows = self.rows

        #  Sentinel.
        assert not self.isempty(), "Empty queue!"

        #  弹出的数据。
        res = [trackers[head][j] for j in range(16)]
        trackers[head] = [[] for j in range(16)]

        #  修改head的位置。
        if head == rows - 1:
            head = 0
        else:
            head += 1

        #  更新属性。
        self.head = head
        self.trackers = trackers


    def enqueue(self, psvalues):
        """
        function:对光敏追踪器增加一行数据psvalues。
        :param psvalues:
        """

        #  取出参数。
        trackers = self.trackers
        rows = self.rows
        head = self.head
        tail = self.tail

        #  如果队列已满，则先从head弹出一行数据。
        if self.isfull():
            self.dequeue()
        #  在tail处插入数据。
        trackers[tail] = [psvalues[i] for i in range(16)]
        #  修改tail的值。
        if tail == rows - 1:
            tail = 0
        else:
            tail += 1

        #  更新属性。
        self.tail = tail
        self.trackers = trackers


        def Isbroken(self, psvalues):
            """
            function: detecting each photosensitive to see whether is good or broken.
            :param self:
            :param psvalues:
            :return:
            """




def GetMudLvl( inputfile, ws ):
    #  新建并初始化光敏追踪器。
    timewindow = 1  # 设定追踪器时间窗长，单位为分钟，最小值为1。
    pst = PsTrackers( timewindow )

    count = 0

    with open( inputfile ) as f:
        while True:
            #  读入光敏数据。
            line = f.readline()  # 读取一行光敏数据（str）。
            #  EOF Sentinel.
            if line == '':
                break
            line = line.split(",")  # 按逗号分割字符串。
            psvalues = [float(value) for value in line]  # 将str转换为float，PhotoSensitive Value。
            #  Collecting the photosensitive values.
            pst.enqueue(psvalues)
            #  检查损坏的光敏。
            pst.Isbroken(psvalues)



            count += 1
            if count == 12:
                break
        #     #  光敏数据写入excel，用于人工检查。
        #     ws.append(psvalues)  # worksheet中写入一行光敏数据。
        # wb.save(inputfile[:-3] + "xlsx")  # 保存为与输入数据文件同名的excel文件。
    f.close()







"""
功能：根据光敏数据，定位随时间变化的泥位点。

Step0.预处理光敏数据：
      选出一个池子，某段时间内的16组光敏数据，保存为txt文档，默认名：PreData02.txt。
      e.g. 选用db_181013/sanchang_db数据中的5号池，共262943个数（大约1个月）。

Step1.
"""

start = time.time()  # 程序开始时间。
#  预处理后的，光敏数据文件名。
inputfile = "PreData02.txt"

#  打开一个excel文件， 用于写入所有的光敏数据。
wb = Workbook()  # 在内存中创建一个workbook对象，而自动创建一个worksheet。
ws = wb.active  # 获取当前活跃的worksheet，默认就是第一个worksheet。


GetMudLvl( inputfile, ws )

end = time.time()  # 程序结束时间。
print(end-start)  # 程序运行时间，单位为秒。


