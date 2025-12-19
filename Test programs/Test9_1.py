def is_positional_power_match(n):
    power = 0
    total = 0
    for i in str(n):
        power += 1
        total += int(i)**power
    return total, total == n

num = int(input("Enter a number: "))
result, is_positional_power_match_num = is_positional_power_match(num)
if is_positional_power_match_num:
    print(f"The digit power sum is {result} and hence the number is a positional power match number")
else:
    print(f"The digit power sum is {result} and hence the number is not a positional power match")