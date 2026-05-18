import os
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, 'working_with_a_file.txt')

file = open(file_path, 'w')

file.write('Hello How are you!\n')
file.write('What did you eat for breakfast\n')

lines = ['The sun is shinning\n', 'The days are too long nowaday\n']

file.writelines(lines)

file = open(file_path, 'r')

content =  file.readline()

print('Using read(): ')
print(content)

content =  file.readline()

print('Using read(): ')
print(content)





