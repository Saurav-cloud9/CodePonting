text = input("Enter a word or a sentence: ")

# Normalize: lowercase and remove spaces
cleaned = "".join(ch.lower() for ch in text if ch.isalnum())

if cleaned == cleaned[::-1]:
    print("Yes! it's a palindrome")
else:
    print("No! it's not a palindrome")