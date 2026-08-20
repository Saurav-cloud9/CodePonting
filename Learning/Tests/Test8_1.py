def total(m):
    total = m + int(str(m)[::-1])
    return total

n = int(input("Enter a number: "))
result = total(n)

x = 0
while result != int(str(result)[::-1]) and x < 50:
    print(result)
    x += 1
    result = total(result)

if result == int(str(result)[::-1]):
    print("The final number", result, "is a palindrome")
else:
    print("This number", result, "could possibly be a Lychrel number")
