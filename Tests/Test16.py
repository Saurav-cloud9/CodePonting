#check for palindrome

def is_palindrome(text):
    text_cleaned = ''.join(char for char in text.lower() if char.isalpha())
    return text_cleaned == text_cleaned[::-1]


while True:
    sentence = input("Enter a word or phrase (or press Enter to quit): ")
    if sentence.strip() == "":
        print("Empty input. Please enter a word or phrase.")
        print("Thank you!")
        break
    if is_palindrome(sentence):
        print(f'{sentence} is a palindrome')
    else:
        print(f'{sentence} is not a palindrome')
    while True:
        play_again = input('Would you like to play again? (y/n):').lower()
        if play_again in ['y','n']:
            break
        print("Please enter 'y' or 'n'.")
    if play_again == 'n':
        print("Thank you!")
        break






