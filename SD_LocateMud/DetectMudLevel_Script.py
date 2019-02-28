from openpyxl import Workbook  # 写入excel用的库
import queue

def GetMudLvl( inputfile, ws ):
    with open(inputfile) as f:
        count = 0
        while True:
            count += 1
            if count == 50:
                break
            #  读入光敏数据。
            line = f.readline()  # 读取一行光敏数据（str）。
            #  EOF Sentinel.
            if line == '':
                break
            line = line.split(",")  # 按逗号分割字符串。
            psvalue = [float(value) for value in line]  # 将str转换为float，PhotoSensitive Value。

            #  光敏数据写入excel，用于人工检查。
            ws.append(psvalue)  # worksheet中写入一行光敏数据。
        wb.save(inputfile[:-3] + "xlsx")  # 保存为与输入数据文件同名的excel文件。
    f.close()





    #   读取污水厂数据。
    # data = xlrd.open_workbook( file )
    # table = data.sheets()[0]
    # rows = table.nrows
    # cols = table.ncols
    #
    # #  设置16个光敏探针。
    # for i in range(16):
    #     #  设定16个光敏check point；
    #     #  每个check point为一个滑动队列，随时间滑动；
    #     #  记录1小时内该光敏接收点的历史纪录，即360条记录。
    #     exec("cp%s=queue.Queue(360) " % i, globals())
    #
    # for i in range(rows):
    #     # 从excel表中取出字符串格式的16个光敏数据。
    #     tmp = table.row_values(i)[2]
    #     #  光敏数据pd（Photosensitive data）转换格式。
    #     pd = [float(item) for item in tmp.split(",")]
    #
    #     #  数据记录到光敏探针中。
    #     for j in range(16):
    #         exec("cp_now = cp%s" % j, globals())
    #         if cp_now.full():
    #             cp_now.get()
    #         else:
    #             cp_now.put(pd[j])
    #         print(cp_now.queue)
    #         break










"""
功能：根据光敏数据，定位随时间变化的泥位点。

Step0.预处理光敏数据：
      选出一个池子，某段时间内的16组光敏数据，保存为txt文档，默认名：PreData02.txt。
"""


#  预处理后的，光敏数据文件名。
inputfile = "PreData02.txt"

#  打开一个excel文件， 用于写入所有的光敏数据。
wb = Workbook()  # 在内存中创建一个workbook对象，而自动创建一个worksheet。
ws = wb.active  # 获取当前活跃的worksheet，默认就是第一个worksheet。
GetMudLvl( inputfile, ws )