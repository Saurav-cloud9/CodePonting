from random import randint

def guess_the_number():
    print('Lets play guess the number game.')
    count = 0
    r = 10
    num = 0
    m = randint(1, 100)
    while count < 10 and m != num:
        try:
            num = int(input(f'Guess a number between 1 and 100. You have {10 - count} attempts left!'))
            count += 1
            if num < 1 or num > 100:
                print('invalid input')
                count -= 1
            elif num == m:
                print('You have made the right guess in', count, 'tries')
            elif num > m:
                print('Your guess is too high')
            else:
                print('Your guess is too low')
        except ValueError:
            print('Invalid input. Please enter an integer.')
    if num != m:
            print('The correct number is', m)

while True:
    guess_the_number()
    answer = input("Play again? y or n")
    if answer == 'y':
        continue
    else:
        print("Thank you for playing")
        break

