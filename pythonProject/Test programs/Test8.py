def total(m):
    total = m + int(str(m)[::-1])
    return total

n = int(input("Enter a number: "))
result = total(n)
if result == int(str(result)[::-1]):
    print("The sum of the number and its reverse is", result, "and it is a palindrome")
else:
    print("The sum of the number and its reverse is", result, "and it is not a palindrome")