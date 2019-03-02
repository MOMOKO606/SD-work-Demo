import time
import math
import numpy as np
from openpyxl import Workbook  # 写入excel用的库


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
        self.brokelist = [False for i in range(16)]  # 损坏光敏列表。
        self.sum = [0.0 for i in range(16)]  # 追踪器的总值。
        self.mean = [0.0 for i in range(16)]  # 追踪器的均值。
        self.stddev = [0.0 for i in range(16)]  # 追踪器的标准差。
        self.max = [float('-inf') for i in range(16)]  # 追踪器的最大值。
        self.min = [float('inf') for i in range(16)]  # 追踪器的最小值。
        self.rows = m
        self.head = 0  # 光敏追踪器的head。
        self.tail = 0  # 光敏追踪器的tail。
        self.count = 0  # 表示追踪器内有多少条数据。



    def reset(self):
        """
        function: 清除追踪器内的所有数据。
        """
        n = 16
        m = self.rows
        self.trackers = [[[] for i in range(n)] for j in range(m)]  # 追踪器初值。
        self.brokelist = [False for i in range(16)]  #  损坏光敏列表。
        self.mean = [0 for i in range(16)]   # 追踪器的均值。
        self.sum = [0 for i in range(16)]  # 追踪器的总值。
        self.stddev = [0 for i in range(16)]   #  追踪器的标准差。
        self.max = [float('-inf') for i in range(16)]  # 追踪器的最大值。
        self.min = [float('inf') for i in range(16)]  # 追踪器的最小值。
        self.head = 0  # 光敏追踪器的head。
        self.tail = 0  # 光敏追踪器的tail。
        self.count = 0  #  表示追踪器内有多少条数据。



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
        return res



    def enqueue(self, psvalues):
        """
        function:对光敏追踪器增加一行数据psvalues。
        :param psvalues: 实时光敏数据。
        """

        #  取出参数。
        trackers = self.trackers
        rows = self.rows
        head = self.head
        tail = self.tail

        #  更新count, sum, mean属性。
        #  如果队列已满，则先从head弹出一行数据。
        popedvalue = []
        if self.isfull():
            popedvalue = self.dequeue()
            self.count = self.rows - 1
            self.sum = [self.sum[i]-popedvalue[i] + psvalues[i] for i in range(16)]
        #  队列未存满时：
        else:
            self.count += 1
            self.sum = [self.sum[i] + psvalues[i] for i in range(16)]
        self.mean = [self.sum[i] / self.count for i in range(16)]

        #  在tail处插入数据。
        trackers[tail] = [psvalues[i] for i in range(16)]
        self.trackers = trackers  # 更新属性。
        #  修改tail的值。
        if tail == rows - 1:
            tail = 0
        else:
            tail += 1
        self.tail = tail  # 更新属性。

        #  更新stddev。
        #  遍历追踪器。
        for j in range(16):
            tmp = 0  # 累加器，初值为0。
            for i in range(0, rows):
                #  Sentinel, 跳过空值。
                if trackers[i][j] == []:
                    continue
                tmp += (trackers[i][j] - self.mean[j]) ** 2
            tmp /= self.count
            self.stddev[j] = math.sqrt( tmp )

        return popedvalue  # 返回弹出的一行数据



    def GetIndices(self):
        """
        function: 得到从tail向head方向，遍历的indices.
        :return: indices数组。
        """
        #  读取参数。
        head = self.head
        tail = self.tail
        rows = self.rows

        #  case1.
        if tail == 0:
            indices = [rows - 1, 0]
        #  case2.
        elif tail > head:
            indices = [tail - 1, head - 1]
        #  case3.head > tail
        else:
            indices = [[tail - 1, -1], [rows - 1, head - 1]]
        return indices



    def Isbroken(self):
        """
        function: detecting each photosensitive to see whether is good or broken.
        """
        rows = self.rows
        brokelist = self.brokelist
        trackers = self.trackers
        indices = self.GetIndices()

        #  对应GetIndices函数中的case1和case2.
        if len(np.array(indices).shape) == 1:

            start = indices[0]
            end = indices[1]

            #  caseA:1分钟内速测(短周期检测)。
            #  当前值与10s前的值，delta超过380，则光敏损坏。
            for j in range(16):
                now = trackers[start][j]
                previous = trackers[start - 1][j]
                #  trackers中只存了一个值的情况。
                if previous == []:
                    previous = now
                if abs(now - previous) >= 380:
                    brokelist[j] = True
                else:
                    brokelist[j] = False

            #  caseB:1分钟以上检测(长周期检测)。
            if rows > 6:
                for j in range(16):
                    #  Sentinel，已在短周期被定位为True的不再检测。
                    if brokelist[j]:
                        continue
                    #  标准差大于150,波动较大，疑似随机值：
                    if self.stddev[j] >= 150:
                        #  检查时间窗内，追踪器数据是否单调递增或递减。
                        #  单调递增，则由泥变水；
                        #  单调递减，则由水变泥。
                        delta = 0.0
                        for i in range(start, end + 1, -1):
                            delta += trackers[i][j] - trackers[i - 1][j]
                        #  变化值相加后取绝对值，距离900较远说明是随机值，即光敏损坏。
                        if abs(delta) < 700:
                            brokelist[j] = True
                        #  泥位快速升降。
                        else:
                            brokelist[j] = False

        #  对应GetIndices函数中的case3.
        else:

            start1 = indices[0][0]
            end1 = indices[0][1]
            start2 = indices[1][0]
            end2 = indices[1][1]

            #  caseA:1分钟内速测(短周期检测)。
            #  当前值与10s前的值，delta超过380，则光敏损坏。
            #  横向检查16个追踪器。
            for j in range(16):
                tmplist = []
                #  纵向从追踪器里找最近的两条数据。
                #  可优化，只读2条。
                for i in range(start1,end1,-1):
                    tmplist.append(trackers[i][j])
                #  如果已经至少找到2条数据：
                if (len(tmplist) >= 2):
                    now = tmplist[0]
                    previous = tmplist[1]
                #  只有一条数据:
                else:
                    now = tmplist[0]
                    previous = trackers[start2][j]
                #  如果10s跳动大于380，则认为是随机值，即光敏损坏。
                if abs( now - previous) > 380:
                    brokelist[j] = True
                else:
                    brokelist[j] = False

            #  caseB:1分钟以上检测(长周期检测)。
            if rows > 6:
                for j in range(16):
                    #  Sentinel，已在短周期被定位为True的不再检测。
                    if brokelist[j]:
                        continue
                    #  标准差大于150，波动较大，疑似随机值：
                    if self.stddev[j] >= 150:
                        #  检查时间窗内，追踪器数据是否单调递增或递减。
                        #  单调递增，则由泥变水；
                        #  单调递减，则由水变泥。
                        delta = 0.0
                        for i in range(start1,end1 + 1, -1):
                            delta += trackers[i][j] - trackers[i - 1][j]
                        for i in range(start2,end2 + 1, -1):
                            delta += trackers[i][j] - trackers[i - 1][j]
                        #  变化值相加后取绝对值，距离900较远说明是随机值，即光敏损坏。
                        if abs(delta) < 700:
                            brokelist[j] = True
                        #  泥位快速升降。
                        else:
                            brokelist[j] = False
        #  更新仪器损坏表。
        self.brokelist = brokelist
        return brokelist



def GetMudLvl( inputfile, ws ):
    #  新建并初始化光敏追踪器。
    timewindow = 5  # 设定追踪器时间窗长，单位为分钟，最小值为1，建议选取3-5。
    pst = PsTrackers( timewindow )
    with open( inputfile ) as f:

        ###  测试用  ###
        timecount = 0
        pre_brokelist = [False for i in range(16)]
        broke_time = [[] for i in range(16)]
        ###  测试用  ###

        while True:

            ###  测试用  ###
            timecount += 1
            ###  测试用  ###

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
            brokelist = pst.Isbroken()

            ###  测试用  ###
            for j in range(16):
                if brokelist[j] != pre_brokelist[j]:
                    broke_time[j].append(timecount)
            pre_brokelist = brokelist[:]
            ###  测试用  ###





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


