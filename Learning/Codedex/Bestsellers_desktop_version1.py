import csv
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, "Bestsellers_desktop_version1.csv")

data_to_write = [
  ['Name', 'Age', 'Grade'],
  ['Alice', 25, 'A'],
  ['Bob', 22, 'B'],
  ['Charlie', 28, 'A+']
]

with open(file_path, 'w+', newline='') as file:
    csv_writer = csv.writer(file)
    csv_writer.writerows(data_to_write)

    file.seek(0)

    csv_reader = csv.reader(file)

    for row in csv_reader:
       print(row)