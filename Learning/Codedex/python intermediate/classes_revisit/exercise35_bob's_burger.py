class Restaurants():
    name = ''
    category = ''
    rating = 0.0
    delivery = False

bobs_burgers = Restaurants()

bobs_burgers.name = "Bob's Restaurant"
bobs_burgers.category = "American Diner"
bobs_burgers.rating = 4.7
bobs_burgers.delivery = False

ghar_ka_dhaba = Restaurants()

ghar_ka_dhaba.name = "Ghar Ka Dhaba"
ghar_ka_dhaba.category = "Desi Restaurant"
ghar_ka_dhaba.rating = 4.8
ghar_ka_dhaba.delivery = True

print(vars(bobs_burgers))
print(vars(ghar_ka_dhaba))

