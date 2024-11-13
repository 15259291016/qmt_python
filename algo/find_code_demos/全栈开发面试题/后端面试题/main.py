def merge_sorted_arrays(a, b):
    # 初始化结果数组 c 和指针 i, j
    c = []
    i, j = 0, 0

    # 逐一比较 a 和 b 中的元素，较小的加入到 c 中
    while i < len(a) and j < len(b):
        if a[i] < b[j]:
            c.append(a[i])
            i += 1
        else:
            c.append(b[j])
            j += 1

    # 如果 a 还有剩余元素，加入到 c 中
    while i < len(a):
        c.append(a[i])
        i += 1

    # 如果 b 还有剩余元素，加入到 c 中
    while j < len(b):
        c.append(b[j])
        j += 1

    return c

# 从终端输入两个已排序的数组
a_input = input("请输入第一个已排序的数组（用逗号分隔每个数字）: ")
b_input = input("请输入第二个已排序的数组（用逗号分隔每个数字）: ")

# 将输入字符串转换为整数数组
a = list(map(int, a_input.split(',')))
b = list(map(int, b_input.split(',')))

c = merge_sorted_arrays(a, b)
print(c)