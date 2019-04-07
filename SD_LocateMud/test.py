def L2Rmoving(start, end, leftkey, A, res):
    """
    function: 从start向end前进，并鉴别每个数据是否发生异常。
    :param start: 输入数据A的起始角标。
    :param end: 输入数据A的终点角标。
    :param leftkey: start左侧，即上一阶段的最后一个正常值。
    :param A: 输入数据。
    :param res: 对应输入数据A的bool数组，True表示该点数据正常，False表示该点数据存在异常2的情况。
                异常2包括：各别光栅损坏，浮泥，泥中含较多的水（简称含水泥）。
    :return:
    """

    #  base case: 已遍历完。
    if start > end:
        return res

    #  循环初值。
    i = start
    rightdelta = A[i] - A[i + 1]
    #  右侧数据与当前数据相差不大, 且没有到右边界，则右移。
    while abs(rightdelta) <= 150 and i < end:
        i += 1
        rightdelta = A[i] - A[i + 1]


    #  右侧数据发生跳跃，鉴别该阶段数据是否正常。
    if abs(rightdelta) > 150:
        leftdelta = A[i] - leftkey
        #  发生相变的正常情况。
        if abs(leftdelta) <= 150 or leftdelta * rightdelta < 0:
            for j in range(start, i + 1):
                res[j] = True
            leftkey = A[i]
        #  可能发生异常2。
        else:
            #  发生异常2。
            if i - start + 1 < 7:
                for j in range(start, i + 1):
                    res[j] = False
            #  不可能连坏7个。
            else:
                for j in range(start, i + 1):
                    res[j] = True
                leftkey = A[i]
    #  跳转到下一阶段。
    return L2Rmoving(i + 1, end, leftkey, A, res)


def AddBound(A):
    n = len(A)
    res = [0.0 for i in range(0, n + 2)]
    res[n + 1] = 900
    for i in range(1, n + 1):
        res[i] = A[i - 1]
    return res


if __name__ == "__main__":
    A1 = [32, 16, 13, 120, 12, 9, 303, 10, 900, 956, 900, 900, 923, 900, 900, 900]
    A2 = [69, 909, 19, 5, 14, 900, 900, 900, 900, 900, 900, 900, 900, 900, 900, 954]
    A3 = [0, 10, 5, 5, 11, 927, 187, 0, 3, 337, 3, 163, 16, 975, 865, 900]
    A4 = [41, 82, 1, 11, 387, 385, 903, 900, 900, 900, 900, 900, 900, 900, 127, 127]
    A5 = [3, 6, 0, 62, 876, 347, 40, 943, 452, 915, 911, 900, 900, 900, 900, 900]

    A = AddBound(A5)
    res = [True for i in range(0, 18)]
    res = L2Rmoving(1, 16, 0, A, res)

    print(res)