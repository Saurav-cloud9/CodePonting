# Instructions
# Now that you can tell the difference between pure and impure functions, let’s try it out.

# Create a pure function to calculate the area of a circle given its radius.

# Define a calculate_circle_area() function that takes the radius of the circle as input.
# Compute the area of the circle using the formula: area=π∗r 
# 2
#  .
# Return the result.

def calculate_circle_area(r):
    area = 3.14*r**2
    return area

c_area = int(input("enter the radius of the circle: "))
result = calculate_circle_area(c_area)
print(result)