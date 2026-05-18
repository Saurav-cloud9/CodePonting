# Instructions
# We've all seen, perhaps bought, one of our favorite products with a "Bestseller" sticker. 🏅

# Let’s write a program to read a CSV file and find the best-selling book of all time. 🔍

# Download this CSV file of all-time bestselling books data!
# Open the Bestseller - Sheet1.csv file in "read" mode.
# Use the CSV reader to navigate through the data and find the book with the highest sales, via the sales in millions column.
# Create a new file called bestseller_info.csv with the CSV writer.
# In the new file, use .writerow() to add new CSV data.
# Up next, let’s learn about what to do in the face of the unexpected, we'll be exploring error handling.

import csv

with open('c:/Users/Saurav/CodePonting/Learning/Codedex/Bestseller - Sheet1.csv', 'r', encoding='utf-8') as file:
    csv_reader = csv.reader(file)

    max = 0
    next(csv_reader)
    for row in csv_reader:
        if float(row[4]) > max:
            max = float(row[4])
            part2 = row
    print(max)

with open('c:/Users/Saurav/CodePonting/Learning/Codedex/bestseller_info.csv', 'w+', encoding='utf-8') as file:
    csv_writer = csv.writer(file) 

    csv_writer.writerow(part2)

    file.seek(0)

    print(file.read())
        




