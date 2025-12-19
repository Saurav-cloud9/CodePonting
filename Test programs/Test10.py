def is_positional_power_match(n):
    # Helper function to extract digits from left to right without using str()
    def extract_digits_left_to_right(n):
        digits = []
        while n > 0:
            digits.append(n % 10)  # Get the last digit
            n //= 10               # Remove the last digit
        return digits[::-1]        # Reverse to get left-to-right order

    digits = extract_digits_left_to_right(n)  # Get digits in correct order

    # Generator expression: digit raised to its position (starting from 1)
    gen = (digit ** (i + 1) for i, digit in enumerate(digits))
    # Example: for 135 → 1^1 + 3^2 + 5^3

    total = sum(gen)              # Sum all the powered digits
    return total, total == n      # Return the sum and whether it matches the original number

# --- Main Program ---

num = int(input("Enter a number: "))  # Take user input and convert to integer

result, is_match = is_positional_power_match(num)  # Call the function and unpack results

# Print result based on whether it's a positional power match
if is_match:
    print(f"The positional power sum is {result}, so {num} is a positional power match number.")
else:
    print(f"The positional power sum is {result}, so {num} is not a positional power match.")