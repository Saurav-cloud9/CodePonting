def add_numbers_recursive(x, y):
    if y == 0:
        return x
    else:
        return add_numbers_recursive(x + 1, y - 1)

# Take input from the user
num1 = 1
num2 = 2

# Call the recursive function to add the two numbers
result = add_numbers_recursive(num1, num2)

# Print the result
print("The sum of", num1, "and", num2, "is", result)