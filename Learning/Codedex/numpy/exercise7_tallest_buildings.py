# Instructions
# The world’s tallest buildings are the following:

# tallest_buildings = np.array([2717, 2227, 2073, 1972, 1966, 1819, 1776])

# Oh wait, all the heights are using feet. Can you convert this array to meters?


# m=ft∗0.3048

# Use basic operations to create a new array with all the measurements in meters.

import numpy as np

tallest_buildings = np.array([2717, 2227, 2073, 1972, 1966, 1819, 1776])

# print(np.round(tallest_buildings*0.3048, 2))

tallest_buildings_new = np.round(tallest_buildings*0.3048, 2)

print(tallest_buildings_new)