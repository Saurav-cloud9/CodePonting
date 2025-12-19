def reverse_and_add_until_palindrome(n, max_iterations=50):
    def is_palindrome(x):
        return str(x) == str(x)[::-1]

    def reverse_and_add(x):
        return x + int(str(x)[::-1])

    steps = 0
    current = n

    while steps < max_iterations:
        current = reverse_and_add(current)
        steps += 1
        if is_palindrome(current):
            return steps, current

    return steps, f"No palindrome found after {max_iterations} iterations. Possibly a Lychrel candidate."

num = int(input("Enter a number: "))
result = reverse_and_add_until_palindrome(num)

if isinstance(result[1], int):
    print(f"Palindrome {result[1]} found in {result[0]} steps.")
else:
    print(result[1])
