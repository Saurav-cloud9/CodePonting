#[1, 2, 2, 3, 3, 3, 4, 4]


#print(max(input("Enter elements separated by spaces: ").split(), key=lambda x: input_list.count(x)))

input_list = input("Enter elements separated by spaces: ").split()
print(max(input_list, key=input_list.count))

