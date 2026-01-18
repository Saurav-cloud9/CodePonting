def reverse_add(n):
    return n + int(str(n)[::-1])

def is_palindrome(n):
    return str(n) == str(n)[::-1]

n = int(input("Enter a number: "))
result = reverse_add(n)
steps = 1

if is_palindrome(result):
    print(f"The sum of the number and its reverse is {result}, and it is a palindrome.")
else:
    print(f"Step {steps}: {result}")
    while not is_palindrome(result) and steps < 50:
        result = reverse_add(result)
        steps += 1
        print(f"Step {steps}: {result}")

    if is_palindrome(result):
        print(f"Finally, we got {result} which is a palindrome after {steps} steps.")
    else:
        print(f"This number {result} could possibly be a Lychrel number (after {steps} steps).")