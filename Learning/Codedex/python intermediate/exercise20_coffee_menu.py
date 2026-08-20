# Instructions
# Who ordered the latte? Probably me. ☕️

# Coffee shops are wonderful places to work and study. Like any small business, coffee shops require management to manage inventory, order processing, sales, and menus. Let's use what our knowledge of Python testing to make sure a coffee menu is up to date.

# First, set up testing:

# Create and save the coffee_menu.py file.
# Next, set up a CoffeeMenu class:

# In the class set up coffee menu items. It should look like this:

class CoffeeMenu:
  def __init__(self):
    self.menu = {
      'espresso': 2.50,
      'latte': 2.75,
      'cappuccino': 3.20,
      'americano': 2.70
    }

# example_object = CoffeeMenu()

# print(example_object.menu['espresso'])