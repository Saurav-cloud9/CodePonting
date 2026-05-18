# Instructions
# Mental math can bring up mixed feelings. A core math concept is that even numbers are integers divisible by 2.

# Let’s practice using list comprehensions to create a list of even numbers from the following list of integers:

# numbers = [57, 10, 82, 36, 89, 46, 13, 23, 92, 48]

# Create a list comprehension that filters the even numbers.
# Print the original range and the list of even numbers.
# Your outcome should look like this:

# Original Numbers: [57, 10, 82, 36, 89, 46, 13, 23, 92, 48]
# Even Numbers: [10, 82, 36, 46, 92, 48]

# Bonus: create and print a list of odd numbers

numbers = [57, 10, 82, 36, 89, 46, 13, 23, 92, 48]

even_result = [x for x in numbers if x % 2 == 0]

odd_result = [y for y in numbers if y % 2 != 0]

print(f'Original Numbers: {numbers}')
print(f'Even numbers: {even_result}')
print(f'Odd numbers: {odd_result}')

