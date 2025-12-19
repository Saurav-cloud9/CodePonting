def sum_of_powers(n):
    power = 1
    temp = 0
    result = 0
    for i in str(n):
        temp = int(i) ** power
        power += 1
        result += temp
    return n == result

n = int(input("Enter a number: "))
print("the result for n is", sum_of_powers(n))