# Instructions
# Let’s experiment with test cases to cover edge cases for two math functions.

# Define an unexpected.py file and copy the following code into it:

# import unittest
# import math

# def get_sqrt(n):
#   return math.sqrt(n)

# def divide(a, b):
#   return a / b

# Next, create a TestUnexpected class inheriting from unittest.TestCase.

# Inside the test class, write test methods to validate different scenarios of the two functions.

# For get_sqrt(), write tests that:

# Validate the function works properly (e.g., get_sqrt(144) returns 12).
# Check that taking the square root of a negative number raises a ValueError.
# For divide(), write tests that:

# Validate the function works properly (e.g., divide(144, 12) returns 12).
# Check that dividing by zero (0) raises a ZeroDivisionError.
# Run this file to ensure the tests work as expected.

import unittest
import math

def get_sqrt(n):
  return math.sqrt(n)

def divide(a, b):
  return a / b

class TestUnexpected(unittest.TestCase):
  def test_get_sqrt(self):
    self.assertEqual(get_sqrt(144), 12)
    with self.assertRaises(ValueError):
      get_sqrt(-144) 

  def test_divide(self):
    self.assertEqual(divide(144, 12), 12)
    with self.assertRaises(ZeroDivisionError):
      divide(144, 0)

if __name__ == '__main__':
  unittest.main()
  