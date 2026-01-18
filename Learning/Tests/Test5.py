def is_sumof_numbers_powers(m):
    x = 1
    total = 0
    for i in str(m):
        total += int(i) ** x
        x += 1
    return total, m == total

n = int(input("Enter a number"))
result, is_true = is_sumof_numbers_powers(n)
while not is_true:
    print(result,)
    n = result
    result, is_true = is_sumof_numbers_powers(n)

print(result)


