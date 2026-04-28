# In the last exercise, we created a Restaurant class.

# In a new file called bobs_burgers.py, create an instance of the Restaurant class called bobs_burgers with the following attributes:

# 'Bob\'s Burgers'
# 'American Diner'
# 4.7
# False
# Once you do that, create two more instances of the Restaurant class with your favorite dinner spots nearby.

# Then, use print(vars()) to output each of the three restaurants!


class Restaurant:
    name = ''
    category = ''
    rating = 0.0
    delivery = False

bobs_burgers = Restaurant()

bobs_burgers.name = 'Bob\'s Burgers'
bobs_burgers.category = 'American Diner'
bobs_burgers.rating = 4.7
bobs_burgers.delivery = False

mc_donalds = Restaurant()

mc_donalds.name = 'Mc Donald\'s'
mc_donalds.category = 'American fast food'
mc_donalds.rating = 4.6
mc_donalds.delivery = True

print(vars(bobs_burgers))
print(vars(mc_donalds))





