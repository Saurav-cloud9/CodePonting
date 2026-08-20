def is_armstrong(m):
    x = len(str(m))
    total = 0
    for i in str(m):
        total += int(i)**x
    return total, total == m

n = int(input("Enter a number: "))
result, is_armstrong = is_armstrong(n)
if is_armstrong:
    print(f"The digit power sum is {result} and hence the number is an armstrong number")
else:
    print(f"The digit power sum is {result} and hence the number is not an armstrong number")