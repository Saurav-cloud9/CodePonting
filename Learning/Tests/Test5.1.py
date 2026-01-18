def digit_power_chain(n):
    def transform(m):
        x = 1
        total = 0
        for i in str(m):
            total += int(i) ** x
            x += 1
        return total

    seen = []
    while n not in seen:
        seen.append(n)
        n = transform(n)

    seen.append(n)  # Include the repeated value or fixed point

    # Detect if it's a fixed point or a cycle
    if seen[-2] == seen[-1]:
        status = "Fixed point reached."
    else:
        status = "Cycle detected."

    return seen, status


# 🔍 Example usage
n = int(input("Enter a number: "))
sequence, outcome = digit_power_chain(n)

print("Digit Power Chain:")
print(" → ".join(map(str, sequence)))
print(outcome)