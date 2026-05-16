import csv
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, 'Bestsellers_desktop_version.csv')

with open(file_path, 'w+', encoding='utf8', newline='') as file:
    file.write('one,two,three,four')
    file.seek(0)
    csv_reader = csv.reader(file)

    print(csv_reader)

    for row in csv_reader:
        print(row)

