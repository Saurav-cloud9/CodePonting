# Fortune Cookie is a small cookie wafer with a piece of paper inside, called a “fortune”, which is usually a Chinese phrase with translation and a list of lucky numbers. They are served in restaurants in the U.S. and Canada. 🥠

# Create a fortune_cookie.py program that gives the user random fortunes.

# Define a function named fortune(). Inside the function, print out a random fortune from the list of options below:

# Don't pursue happiness – create it.
# All things are difficult before they are easy.
# The early bird gets the worm, but the second mouse gets the cheese.
# Someone in your life needs a letter from you.
# Don't just think. Act!
# Your heart will skip a beat.
# The fortune you search for is in another cookie.
# Help! I'm being held prisoner in a Chinese bakery!
# Make sure to use the random module's random.randint() and an if/elif/else.

# Then, call the fortune() function three times and see what you get!

# Bonus: If you're daring, rewrite the function without an if/elif/else.

# import random

# def fortune():
#     random_fortune = ["Don't pursue happiness – create it.",
#     "All things are difficult before they are easy.",
#     "The early bird gets the worm, but the second mouse gets the cheese.",
#     "Someone in your life needs a letter from you.",
#     "Don't just think. Act!",
#     "Your heart will skip a beat.",
#     "The fortune you search for is in another cookie.",
#     "Help! I'm being held prisoner in a Chinese bakery!"]

#     random_cookie = random.randint(0, 7)
#     print(random_fortune[random_cookie])

# fortune()

import random

def fortune():
    random_fortune = ["Don't pursue happiness – create it.",
    "All things are difficult before they are easy.",
    "The early bird gets the worm, but the second mouse gets the cheese.",
    "Someone in your life needs a letter from you.",
    "Don't just think. Act!",
    "Your heart will skip a beat.",
    "The fortune you search for is in another cookie.",
    "Help! I'm being held prisoner in a Chinese bakery!"]

    random_cookie = random.randint(0, 7)
    return random_fortune[random_cookie]

fortune_variable = fortune()
print(fortune_variable)


