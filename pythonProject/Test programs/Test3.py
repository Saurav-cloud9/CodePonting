from random import randint

print("Welcome to the Number Guessing Game!")
print("I'm thinking of a number between 1 and 100...")

attempts = 0
n = 0
r = randint(1, 100)
while n != r:
    n = int(input("Take a guess: "))
    attempts += 1
    if n < r and r - n > 20:
        print("the guess is too low")
    if n < r and r - n < 10:
        print("you are getting close")
    if n < r and 20 >= r - n >= 10:
        print("you are somewhat close")
    if n > r and n - r > 20:
        print("the guess is too high")
    if n > r and n - r < 10:
        print("you are getting close")
    if n > r and 20 >= n - r >= 10:
        print("you are somewhat close")
    if n == r:
        print(f"🎉 Congratulations! You guessed the number in {attempts} attempts.")
