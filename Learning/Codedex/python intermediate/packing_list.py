# Instructions
# Moving day is almost here! As you gather your belongings, the thought of packing everything can feel overwhelming. 😥

# Using what we learned about files in Python, let’s make a program to help manage your packing list.

# First, in a .py file, import the csv module. Then, paste the following:

# data = [
#   ['Item', 'Quantity'],
#   ['Blender', 2],
#   ['Posters', 30],
#   ['Shoes', 2]
# ]

# We're gonna use this data to make a CSV file!

# Next, create a try-except statement. For the try block:

# Try opening a packing_list.csv file in 'r' "read" mode.
# Create a reader object for the CSV file.
# Loop through and print() each row in the object .
# For the except block:

# Specify the FileNotFoundError.
# Print "Packing list file not found. Creating a new one."
# Open a new packing_list.csv file in 'w' "write" mode.
# Create a writer object of the CSV file.
# Use the object's .writerows() method to process the data variable.
# At this point, go ahead and save your .py file and run your program once.

# Look in your file system and you should see a new CSV file in the same folder as this file.

# Nice, you did it! Go ahead and add more things to your packing list and share with your friends to have them double check!

# Happy packing! 📦

import csv
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, 'packing_list.csv')

data = [
  ['Item', 'Quantity'],
  ['Blender', 2],
  ['Posters', 30],
  ['Shoes', 2]
]

data1 = [
  ['Fridge', 1],
  ['TV', 1],
  ['Sofa', 2]
]

try:
    with open(file_path, 'r', encoding='utf-8', newline='') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            print(row)

except FileNotFoundError:
    print("Packing list file not found. Creating a new one.")
    with open(file_path, 'w+', newline='') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerows(data)
 
with open(file_path, 'a+', encoding='utf-8', newline='') as file:
        if file:
            csv_writer = csv.writer(file)
            csv_writer.writerows(data1)

        file.seek(0)
        csv_reader = csv.reader(file)
        for row in csv_reader:
            print(row)




