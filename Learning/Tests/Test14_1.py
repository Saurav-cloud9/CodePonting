from random import randint

def guess_the_number():
    print("Let's play the Guess the Number game!")
    count = 0
    num = 0
    target = randint(1, 100)
    while count < 10 and num != target:
        try:
            num = int(input(f"Guess a number (1-100, {10 - count} attempts left): "))
            count += 1
            if num < 1 or num > 100:
                print("Please enter a number between 1 and 100.")
                count -= 1
                continue
            if num == target:
                print(f"Congratulations! You guessed it in {count} tries!")
            elif num > target:
                print("Your guess is too high.")
            else:
                print("Your guess is too low.")
        except ValueError:
            print("Invalid input. Please enter an integer.")
            continue
    if num != target:
        print(f"Out of attempts! The correct number was {target}.")

while True:
    guess_the_number()
    answer = input("Play again? (y/n): ").lower()
    if answer != 'y':
        print("Thank you for playing!")
        break