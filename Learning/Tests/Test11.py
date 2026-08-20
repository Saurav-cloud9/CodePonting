def is_positional_power_match(n):
    def extract_digits_left_to_right(m):
        if m == 0:
            return[0]
        digits = []
        while m > 0:
            digits.append(m % 10)
            m //= 10
        return digits[::-1]

    if n < 0:
        return None, False

    digits = extract_digits_left_to_right(n)

    total = sum(digit**i for i, digit in enumerate(digits, start=1))

    return total, total == n

def find_all_matches(k):
    z = []
    limit = 1
    while limit < k:
        x, y = is_positional_power_match(limit)
        if y:
            z.append(limit)
        limit += 1
    return z

num = int(input('Enter the limit:'))
print(f"Below is the list of positional power match between 1 and {num}:")
matches = find_all_matches(num)
print(matches)


