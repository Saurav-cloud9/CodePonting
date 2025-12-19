def is_armstrong(n):
    x = len(str(n))
    total = 0
    for i in str(n):
        total += pow(int(i), x)
    return total == n

n = int(input("Enter a number: "))
if is_armstrong(n):
    print("It is an armstrong number")
else:
    print("It is not an armstrong number")

