import random

words = ['apple','orange','banana','mango']
while True:
    print("Welcome to Hangman!")
    chosen_word = random.choice(words)
    print(chosen_word)
    while True:
        play_again = input("Would you like to play again? (y/n):").lower()
        if play_again in ['y','n']:
            break
        print("Please enter 'y' or 'n'.")
    if play_again == 'n':
        print('Thanks for playing!')
        break
