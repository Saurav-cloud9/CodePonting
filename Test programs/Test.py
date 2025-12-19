def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

def is_special_prime(n):
    return is_prime(n) and is_prime(sum(int(d) for d in str(n)))

# Driver code
n = int(input("Enter a number: "))
if is_special_prime(n):
    print(f"{n} is a special prime!")
else:
    print(f"{n} is not a special prime.")