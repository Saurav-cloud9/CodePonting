import random

words = ['apple','orange','banana','mango']
while True:
    print("Welcome to Hangman!")
    secret_word = random.choice(words)
    display = ['_' for _ in secret_word]
    incorrect_guesses = 0
    max_guesses = 6
    guessed = set()
    while ''.join(display) != secret_word and incorrect_guesses < max_guesses:
        print(' '.join(display))
        while True:
            guess = input("Guess a letter: ").lower()
            if len(guess) == 1 and guess.isalpha():
                break
            print("Please enter a single letter.")

        if guess in guessed:
            print(f"You have already guessed {guess}.")
            continue

        guessed.add(guess)
        for index, value in enumerate(secret_word):
            if guess == value:
                display[index] = guess

        if guess in secret_word:
            print(f"Good guess!")

        if guess not in secret_word:
            incorrect_guesses += 1
            print(f"Sorry, {guess} is not in the word. You have {max_guesses - incorrect_guesses} guesses left.")

        if ''.join(display) == secret_word:
            print(f"You win! {secret_word} is the right word")
            break
        elif incorrect_guesses == max_guesses:
            print(f"Game over! The word was: {secret_word}")
            break

    while True:
        play_again = input("Would you like to play again? (y/n):").lower()
        if play_again in ['y','n']:
            break
        print("Please enter 'y' or 'n'.")

    if play_again == 'n':
        print('Thanks for playing!')
        break

