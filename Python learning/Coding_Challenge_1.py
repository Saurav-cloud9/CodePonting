#Challenge: Number Explorer
#Brief: Ask the user to enter a list of numbers (space-separated),
# validate the input, then compute and print sum, count, average,
# minimum and maximum. Allow the user to type q to quit. Handle invalid
# entries by asking again.


def validate(user_num):
    numbers = user_num.split()
    #return numbers
    final_list = []
    is_valid = True
    for n in numbers:
        if n.strip().lstrip('-').isdigit():
            final_list.append(int(n))
        else:
            return "Invalid input. Please enter only numbers separated by spaces."
            is_valid = False
            break
    if is_valid:
        return "valid list"

def add(user_num):
    numbers = user



num = input("Enter a list of numbers separated by spaces (or 'q' to quit): ")
print(validate(num))


