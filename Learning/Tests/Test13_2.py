num_list = list(map(int, input("Enter the numbers with spaces:").split()))
even_num = list(num for num in num_list if num % 2 == 0)
print(even_num)