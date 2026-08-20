sentence = input("Enter a sentence: ")
words = sentence.split()
reverse_words = " ".join(ch[::-1] for ch in words)
print(reverse_words)