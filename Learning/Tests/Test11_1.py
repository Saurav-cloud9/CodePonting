def is_positional_power_match(n, verbose=False):
    def extract_digits_left_to_right(m):
        if m == 0:
            return [0]
        digits = []
        while m > 0:
            digits.append(m % 10)
            m //= 10
        return digits[::-1]

    if n < 0:
        return None, False

    digits = extract_digits_left_to_right(n)

    # Calculate each term and total
    terms = []
    values = []
    total = 0
    for pos, digit in enumerate(digits, start=1):
        val = digit ** pos
        total += val
        terms.append(f"{digit}^{pos}")
        values.append(str(val))

    if verbose:
        expr = " + ".join(terms)
        evaled = " + ".join(values)
        print(f"{n}: {expr} = {evaled} = {total}")

    return total, total == n


def find_all_matches(k):
    matches = []
    for num in range(1, k):
        total, is_match = is_positional_power_match(num)
        if is_match:
            matches.append(num)
    return matches


# --- Main ---
limit = int(input("Enter the limit: "))
print(f"\nPositional power match numbers between 1 and {limit}:\n")

matches = find_all_matches(limit)

# Print each match with breakdown
for m in matches:
    is_positional_power_match(m, verbose=True)