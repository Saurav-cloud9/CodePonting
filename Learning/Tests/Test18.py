# input = [1, 2, 2, 3, 1, 4]
# output = [1, 2, 3, 4]

while True:
    num_list = [1, 2, 2, 2, 3, 1, 4]
    final_list = set()
    for i in range(len(num_list)):
        for j in range(len(num_list)):
            if num_list[i ] != num_list[j]:
                break

    print(f"The deduplicated list is {final_list}")

    while True:
        play_again = input("Do you want to play again? (y/n)").lower()
        if play_again in ['y', 'n']:
            break
        print("Please enter y or n")

    if play_again == 'n':
        break