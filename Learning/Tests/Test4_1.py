def sum_of_powers_verbose(n):
    power = 1
    result = 0
    for i in str(n):
        result += int(i) ** power
        power += 1
    return result, n == result

n = int(input("Enter a number: "))
sum_of_powers_verbose(n)

total, is_match = sum_of_powers_verbose(n)
print(f"Sum of powered digits: {total}")
print(f"Does it match the original number? {is_match}")
