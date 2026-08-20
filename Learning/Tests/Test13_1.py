sentence = input("Enter a sentence: ")
words = sentence.split()
reverse_words = " ".join(words[::-1])
print(reverse_words)