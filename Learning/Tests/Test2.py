def digit_frequency(n):
    frequency = {}
    for digit in str(n):
        if digit in frequency:
            frequency[digit] += 1
        else:
            frequency[digit] = 1
    return frequency

n = int(input("Enter a number: "))
print("The digit frequency of each digit is", digit_frequency(n))