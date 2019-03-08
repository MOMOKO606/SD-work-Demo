import time
import math
import numpy as np
from openpyxl import Workbook  # 写入excel用的库。
import openpyxl.styles as sty  # 修改excel颜色。


class PsTrackers( list ):
    """
    定义16个光敏追踪器的类。
    """
    def __init__(self, timewindow):
        """
        function: 初始化16个光敏追踪器，即(timewindow*6) * 16的空table, 可视为是16个队列组成的table。
        :param timewindow: 追踪多长时间的光敏值，单位为分钟，至少1分钟，建议3分钟。
        """

        #  Sentinel.
        assert timewindow >= 1, "光敏追踪器时间窗至少为1分钟。"

        list.__init__([])  # 继承list类。
        m = timewindow * 6 + 1  # 光敏追踪器的行数, 加1是由于队列的结构。
        n = 16
        self.trackers = [[[] for i in range(n)] for j in range(m)]  # 追踪器初值。
        self.brokelist = [False for i in range(16)]  # 损坏光敏列表。
        self.brokegratings = [False for i in range(16)]  # 光栅损坏的光敏列表。
        self.gratingcount = [0.0 for i in range(16)]  # 判断光栅是否损坏的辅助数组。
        self.sum = [0.0 for i in range(16)]  # 追踪器的总值。
        self.mean = [0.0 for i in range(16)]  # 追踪器的均值。
        self.stddev = [0.0 for i in range(16)]  # 追踪器的标准差。
        # self.max = [float('-inf') for i in range(16)]  # 追踪器的最大值。
        # self.min = [float('inf') for i in range(16)]  # 追踪器的最小值。
        self.rows = m  # 由timewindow转换的行数。
        self.head = 0  # 光敏追踪器的head。
        self.tail = 0  # 光敏追踪器的tail。
        self.count = 0  # 表示追踪器内目前存有多少条数据。



    def reset(self):
        """
        function: 清除追踪器内的所有数据。
        """
        n = 16
        m = self.rows
        self.trackers = [[[] for i in range(n)] for j in range(m)]  # 追踪器初值。
        self.brokelist = [False for i in range(16)]  #  损坏光敏列表。
        self.brokegratings = [False for i in range(16)]  # 光栅损坏的光敏列表。
        self.gratingcount = [0.0 for i in range(16)]  # 判断光栅是否损坏的辅助数组。
        self.mean = [0 for i in range(16)]   # 追踪器的均值。
        self.sum = [0 for i in range(16)]  # 追踪器的总值。
        self.stddev = [0 for i in range(16)]   #  追踪器的标准差。
        # self.max = [float('-inf') for i in range(16)]  # 追踪器的最大值。
        # self.min = [float('inf') for i in range(16)]  # 追踪器的最小值。
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

        #  检测弹出的数据是否包含光栅损坏的光敏。
        for j in range(16):
            if j == 0:  # 左边界情况。
                left = True
                right = (res[j + 1] - res[j]) > 150
            elif j == 15:  # 右边界情况。
                right = True
                left = (res[j - 1] - res[j]) > 150
            else:
                left = (res[j - 1] - res[j]) > 150
                right = (res[j + 1] - res[j]) > 150
            #  当角标为j的光敏值小于左右两边光敏值时,疑似光栅损坏；
            #  因为是弹出该数据，所以对应gratingcount减1。
            if left and right:
                self.gratingcount[j] -= 1

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

        #  检测插入的数据是否包含光栅损坏的光敏。
        for j in range(16):
            if j == 0:  # 左边界情况。
                left = True
                right = (psvalues[j + 1] - psvalues[j]) > 150
            elif j == 15:  # 右边界情况。
                right = True
                left = (psvalues[j - 1] - psvalues[j]) > 150
            else:
                left = (psvalues[j - 1] - psvalues[j]) > 150
                right = (psvalues[j + 1] - psvalues[j]) > 150
            #  当角标为j的光敏值小于左右两边光敏值时,疑似光栅损坏；
            #  因为是插入该数据，所以对应gratingcount加1
            if left and right:
                self.gratingcount[j] += 1
                #  在历史数据中，光栅疑似故障的比例大于等于83%，则认为光栅损坏。
                if self.gratingcount[j] / self.count >= 5/6:
                    self.brokegratings[j] = True
                else:
                    self.brokegratings[j] = False

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
        function: 得到从tail向head方向的角标indices.
        :return: indices数组。
        """
        #  读取参数。
        head = self.head
        tail = self.tail
        rows = self.rows

        #  case1.queue第一次插满后，又插入一条数据，tail回到0角标的情况。
        if tail == 0:
            indices = [rows - 1, 0]
        #  case2.queue不满时。
        elif tail > head:
            indices = [tail - 1, head - 1]
        #  case3.head > tail，除case1外，queue插满时还在继续插入数据的情况。
        else:
            indices = [[tail - 1, -1], [rows - 1, head - 1]]
        return indices



    def Isbroken(self):
        """
        function: detecting each photosensitive to see whether is good or broken.

        光敏完全损坏：
        检查1.检测当前光敏值与10s前光敏值的差值，大于380认为是随机值，即光敏损坏。
        检查2.检查追踪器中的标准差。如果光敏损坏，会产生0到1000的随机值，其随机分布标准差在280左右。
             所以当追踪器中的标准差接近280时，说明该光敏值是随机的，即光敏损坏。
             但是，如果泥位迅速增高或下降时，也有可能产生0，200，400，600，... , 900的情况。
             这种情况的标准差较大，但其两两光敏值的差值是同一方向的，也就是说delta差值相加应该在900或-900左右。
             所以通过delta值相加来判断是否属于该情况。

        光敏中有光栅损坏：
        检测是否有值总低于左右两边的光敏值。

        return: 完全损坏的光敏列表brokelist，有光栅损坏的光敏列表brokegratings.
        """

        #  载入数据。
        rows = self.rows
        brokelist = self.brokelist
        brokegratings = self.brokegratings
        trackers = self.trackers

        #  定义常量
        STANDARD_STDDEV = 250  # 0-900随机分布的标准差。

        #  首先要知道从近到远的历史数据顺序，
        #  即通过GetIndices函数得到从tail到head的角标。
        indices = self.GetIndices()
        #  对应GetIndices函数中的case1和case2.
        if len(np.array(indices).shape) == 1:
            start = indices[0]
            end = indices[1]

            #  检查光敏是否完全损坏。

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
                    #  标准差大于STANDARD_STDDEV,波动较大，疑似随机值：
                    if self.stddev[j] >= STANDARD_STDDEV:
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
                    #  标准差大于STANDARD_STDDEV，波动较大，疑似随机值：
                    if self.stddev[j] >= STANDARD_STDDEV:
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



def FuzzyInterval(brokelist, brokegratings, psvalues):
    """
    function:根据当前的16个光敏值判断泥面位于的区间。
    :param brokelist: 当前损坏的光敏列表。
    :param brokegratings: 光栅存在问题的光敏列表。
    :param psvalues: 当前的光敏值。
    :return: 泥位位于的光敏区间。
    """

    #  规则：
    #  （1）数据由左向右表示由低到高，即i = 0表示最低处的光敏，i = 15表示最高处的光敏；
    #  （2）泥只可能由下向上，即0是从psvalues数组的左侧开始，特殊情况为最高处有浮泥，浮泥较薄（即最右端一点为0）；
    #  （3）光敏值小于50为泥；
    #  （4）光敏值位于[50,200]为泥水混合物；
    #  （5）光敏值大于200为水；
    #  （6）光敏有损坏则右移一位。

    #  所有光敏值都小于50。
    l = 15
    for i in range(16):
        #  如果i处的光敏有损坏，则右移动一位。
        if brokelist[i] or brokegratings[i]:
            continue
        #  确定纯泥界面:
        if psvalues[i] >= 50:
            #  如果最低端光敏值即大于50，则认为纯泥界面在最低光敏处。
            if i == 0:
                l = 0
            else:
                # 如果上一位光敏损坏。
                if brokelist[i - 1] or brokegratings[i - 1]:
                    l = i
                else:  # 如果上一位光敏没有损坏。
                    l = i - 1
            break


    #  所有光敏值都小于200。
    r = 15
    for i in range(l, 16):
        #  如果i处的光敏有损坏，则右移动一位。
        if brokelist[i] or brokegratings[i]:
            continue
        #  确定泥水混合物界面：
        if psvalues[i] >= 200:
            #  如果最低端光敏值即大于200，则认为泥水混合物界面在最低光敏处。
            if i == 0:
                r = 0
            else:
                r = i
            break

    return [l, r]


def GetMudLvl( inputfile ):
    """
    function: 根据光敏追踪器类，预处理后的历史光敏数据，计算从泥到水的区间。
    :param inputfile: 预处理后的历史光敏数据，文本文件。
    :return: 显示全部历史光敏数据的excel文件，用红色标出泥水区间，绿色为光栅损坏的光敏，紫色为损坏的（不可靠）光敏值。
    """

    #  新建并初始化光敏追踪器。
    timewindow = 3  # 设定追踪器时间窗长，单位为分钟，最小值为1，建议选取3-5。
    pst = PsTrackers( timewindow )

    #  打开一个excel文件， 用于写入所有的光敏数据。
    wb = Workbook()  # 在内存中创建一个workbook对象，而自动创建一个worksheet。
    ws = wb.active  # 获取当前活跃的worksheet，默认就是第一个worksheet。

    with open( inputfile ) as f:
        ###  测试用  ###
        timecount = 0
        ###  测试用  ###
        while True:
            ###  测试用  ###
            timecount += 1
            ###  测试用  ###

            if timecount == 49927:
                print("Bianlong")

            # 读入光敏数据。
            line = f.readline()  # 读取一行光敏数据（str）。
            #  EOF Sentinel.
            if line == '':
                break
            line = line.strip('\n')  # 删除换行符。
            line = line.split(",")  # 按逗号分割字符串。
            #  将str转换为float，PhotoSensitive Value。
            #  "000"表示1000。
            psvalues = [float(str) if str != "000" else 1000 for str in line]
            #  Collecting the photosensitive values.
            pst.enqueue(psvalues)
            #  纵向检测：检查损坏的光敏。
            brokelist = pst.Isbroken()
            brokegratings = pst.brokegratings
            #  横向检测：计算泥位区间。
            mudinterval = FuzzyInterval(brokelist, brokegratings, psvalues)

            print(timecount,mudinterval)

            #  光敏数据写入excel，用于人工检查。
            ws.append(psvalues)  # worksheet中写入一行光敏数据。
            for j in range(16):
                #  将光栅损坏的光敏标记成绿色。
                if brokegratings[j]:
                    ws.cell(row = timecount, column = j + 1).fill = \
                        sty.PatternFill(fill_type = "solid", fgColor = "0000FF00")
                #  将完全损坏的光敏标记成紫色。
                if brokelist[j]:
                    ws.cell(row = timecount, column = j + 1).fill = \
                        sty.PatternFill(fill_type = "solid", fgColor = "007A378B")
            #  将泥位区间标记为红色。
            for i in range(mudinterval[0], mudinterval[1] + 1):
                ws.cell(row = timecount, column = i + 1).fill = \
                    sty.PatternFill(fill_type = "solid", fgColor = "00FF0000")
        wb.save(inputfile[:-3] + "xlsx")  # 保存为与输入数据文件同名的excel文件。



"""
脚本功能：根据历史数据库中的光敏数据，定位随时间变化的泥位点。

Step0.预处理光敏数据：
      (1)选出一个池子，某段时间内的16组光敏数据，保存为txt文档.
      e.g. 选用db_181013/sanchang_db数据中的5号池，共262943个数（大约1个月），默认命名为PreData02.txt。
Step1.定义光敏追踪器类，纵向追踪历史数据。
Step2.首先通过光敏追踪器过滤掉当前时刻的问题光敏，问题光敏有2种情况：
      （1）光敏彻底坏掉，跳随机值。
      （2）光敏中的个别光栅坏掉，其数值总比正常值低200+。
      再横向计算污泥区间。
Step3.跟踪污泥区间，连续的污泥区间应该是连续的。
"""

start = time.time()  # 程序开始时间。

#  预处理后的光敏数据文件名。
inputfile = "PreDataFull.txt"

#  调用函数计算泥位。
#  输出excel文件，用颜色标识泥位区间，损坏的光敏。
GetMudLvl( inputfile )

end = time.time()  # 程序结束时间。
#  显示程序的运行时间，单位为秒。
print(end-start)


