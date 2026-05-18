class Student: 
  def __init__(self, name, year, gpa, enrolled):
    self.name = name
    self.year = year
    self.gpa = gpa
    self.enrolled = enrolled

daniel = Student('Daniel Li', 10, 4.0, True)

ladybird = Student('Christine McPherson', 12, 4.0, True)
kyle = Student('Kyle Scheible', 12, 3.4, True)

print(vars(ladybird))
print(vars(kyle))

# Output: 
# {'name': 'Christine McPherson', 'year': 12, 'gpa': 4.0, 'enrolled': True}
# {'name': 'Kyle Scheible', 'year': 12, 'gpa': 3.4, 'enrolled': True}

# Instructions
# Ever wonder how many people live in New York City? What about London?

# Create a favorite_cities.py program.

# Let's make a City class that uses the __init__() method to define the following attributes:

# name (string)
# country (string)
# population (integer rounded to the nearest thousand people)
# landmarks (list of strings)
# Next, create an object for your hometown and assign the attributes above.

# Lastly, create another object for the city that you've always wanted to visit!

# Bonus: Add 2-3 more attributes, like nickname, founding year, mayor, etc.

class City: 
  def __init__(self, name, country, population, landmarks):
    self.name = name
    self.country = country
    self.population = population
    self.landmarks = landmarks

Dehradun_City = City('Dehradun', 'India', 855000, ['Clock Tower', 'Robber\'s Cave', 'Forest Research Institute'])
Shimla_City = City('Shimla', 'India', 252000, ['Jakhu Temple'])

print(vars(Dehradun_City))
print(vars(Shimla_City))



