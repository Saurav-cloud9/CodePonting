class Pokemon:
  def __init__(self, entry, name, types, description, is_caught):
    self.entry = entry
    self.name = name
    self.types = types
    self.desciption = description
    self.is_caught = is_caught

  def speak(self):
    print(f"{self.name} {self.name}")
  
  def display_details(self):
    print(f"{self.entry} {self.name}")

Pikachu = Pokemon(25, Pikachu, Electric, 'It has small electric sacs on both its cheeks. If threatened, it looses electric charges from the sacs.', true)

Pikachu.display_details()


