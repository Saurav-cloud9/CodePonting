# Instructions
# If you’ve ever signed up for Discord or Reddit, you probably got a random username. Odds are those sites are using list comprehensions to generate fantastical names for new users.

# Let’s generate our usernames with functional programming! Here's some code to get us started:

# Each name will be a combination of a prefix and a suffix randomly chosen from predefined lists.

# Under the suffixes list, define a capitalize_suffix() function that returns a capitalized name parameter. Then, use the map() function to apply capitalize_suffix() to each item in the suffix list and store in a variable.

# Note: Remember to use the list() function (e.g., list(map(capitalize_suffix, suffixes))).

# Next, use list comprehensions to generate 10 fantasy names, using create_fantasy_name(). Save to a new random_names list.

# Then, define the following pure functions:

# fire_in_name(name) that returns True if 'Fire' is in name.
# concatenate_names(name1, name2) that returns a string of name1 + name2.
# Next, do the following:

# Use filter() and apply fire_in_name() to the random_names list.
# Use reduce() and apply concatenate_names() to the filtered names.
# Note: Don't forget that we need the functools module to use reduce().

# Lastly, define one more function, display_name_info(), that does the following:

# Prints the generated fantasy names with a for loop.
# Prints the filtered names that include 'Fire'.
# Prints the reduced names.
# Go ahead and use display_name_info(). What names did you get? Feel free to share with your friends on Twitter!

import random
from functools import reduce

prefixes = ['Mystic', 'Golden', 'Dark', 'Shadow', 'Silver']
suffixes = ['storm', 'song', 'fire', 'blade', 'whisper']

def create_fantasy_name(list_1, list_2):
  return random.choice(list_1) + ' ' + random.choice(list_2)

def capitalize_suffix(name):
  return name.capitalize()

capital_suffix = list(map(capitalize_suffix, suffixes))
# print(capital_suffix)

random_names = [create_fantasy_name(prefixes, capital_suffix) for x in range(10)]
# print(random_names)

def fire_in_name(name):
  return 'Fire' in name

def concatenate_names(name1, name2):
  return name1 + name2

filtered_names = list(filter(fire_in_name, random_names))
# print(list(filtered_names))

reduced_names = reduce(concatenate_names, filtered_names, '')

def display_name_info():
  print("**RANDOM NAMES**")
  for r in random_names:
    print(r)
#   print(random_names)
  print("**FILTERED NAMES**")
  for f in filtered_names:
    print(f)
#   print(filtered_names)
  print("**REDUCED NAMES**")
#   for r in reduced_names:
#     print(r)
  print(reduced_names)


display_name_info()