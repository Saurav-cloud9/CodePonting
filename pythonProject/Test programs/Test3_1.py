import random

def number_guessing_game():
    secret_number = random.randint(1, 100)
    attempts = 0
    guessed_correctly = False

    print("Welcome to the Number Guessing Game!")
    print("I'm thinking of a number between 1 and 100...")

    while not guessed_correctly:
        try:
            guess = int(input("Take a guess: "))
            attempts += 1

            if guess < secret_number:
                print("Too low. Try again!")
            elif guess > secret_number:
                print("Too high. Try again!")
            else:
                guessed_correctly = True
                print(f"🎉 Congratulations! You guessed the number in {attempts} attempts.")
        except ValueError:
            print("Please enter a valid integer!")

# Run the game
number_guessing_game()