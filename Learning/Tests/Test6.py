def sum_of_no_and_reverse(m):
    x = str(m)[::-1]
    y = int(x)
    total = m + y
    return total

n = int(input("enter the number"))
result = sum_of_no_and_reverse(n)
print(result)

if str(n) == str(n)[::-1]:
    print("Hey man! this number is a palindrome")

