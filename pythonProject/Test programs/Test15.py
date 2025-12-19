def find_longest_word(sentence):
    words = sentence.split()
    max_length = 0
    longest_word = ""
    for word in words:
        word_length = len(word)
        if word_length > max_length:
            max_length = word_length
            longest_word = word
    if not words:
        return None
    else:
        return longest_word, max_length

while True:
    sent = input("Enter a sentence: ")
    if sent.strip() == '':
        break
    result, length = find_longest_word(sent)
    print(f"Longest word: {result}, Length: {length}")
    while True:
        play_again = input('Do you want to continue? y/n ').lower()
        if play_again in ['y' , 'n']:
            break
        print("Please enter 'y' or 'n'.")
    if play_again == 'n':
        print('Thank you!')
        break