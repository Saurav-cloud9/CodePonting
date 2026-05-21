# 17. Assertions
# # TestCase Class
# Python's unittest framework uses a special TestCase class to organize and execute individual test methods. Each test method represents a specific scenario or behavior (or unit) that we want to test in our code.

# We will learn about setting up test cases and using important attributes in a TestCase instance.

# Let's see how test cases are set up and learn about important attributes available to use within a TestCase instance.

# Remember the add() function test from the last exercise? Let's build it! We start by creating a test case class TestAddFunction that inherits from unittest.TestCase.

import unittest

# Function to test: add two numbers
def add(a, b):
  return a + b

# Test case class for testing the add function
class TestAddition(unittest.TestCase):

  # Test methods

# When you create a test class that inherits from unittest.TestCase, each test method becomes an individual test case. Before running a test method, unittest initializes a new instance of the TestCase class.

# Test methods within a TestCase class are prefixed with test_ and are automatically discovered and executed by the unittest framework.

# During initialization:

# unittest prepares the test environment for the upcoming test method.
# Any attributes defined within the TestCase class are initialized.
# # Assert Methods
# Any TestCase instance comes with some helpful methods for testing:

# self.assertEqual(): Checks if two values are equal.
# self.assertTrue() and self.assertFalse(): Verifies boolean conditions.
# self.assertIn() and self.assertNotIn(): Checks for membership in a collection.
# The self refers to the actual TestCase instance.

# Let's look at the code example below to understand TestCase initialization and attributes:

import unittest

# Function to test: add two numbers
def add(a, b):
  return a + b

class MyTestCase(unittest.TestCase):
  def test_addition(self):
    result = 2 + 3
    self.assertEqual(result, 5)       # Verify that 2 + 3 equals 5

  def test_string_length(self):
    text = 'Hello, World!'
    self.assertEqual(len(text), 13)   # Verify string length

  def test_text_contains_word(self):
    text = 'Hello, World!'
    self.assertTrue('Hello' in text)  # Verify that 'Hello' is in the text
    self.assertIn('World', text)      # Verify that 'World' is in the text

if __name__ == '__main__':
  unittest.main()

# MyTestCase inherits from the TestCase class and has two test methods (test_addition and test_string_length).
# Each test method uses assertion methods (self.assertEqual()) to check specific conditions and ensure that our code behaves correctly.
# The if-statement at the bottom checks if the test file is being run. If so,unittest uses the .main() method and executes the test methods within MyTestCase.

# Instructions
# Time to practice with strings! You will:

# Write test cases to validate specific behaviors.
# Use assertion methods to verify expected outcomes.
# First, let's start by creating a new string_utils.py file.

# Next, define the following functions:

def reverse_string(s):
  return s[::-1]

def capitalize_string(s):
  return s.capitalize()

def is_capitalized(s):
  return s[0].isupper()

# Now, let's write some unit tests. Create another Python file named test_string_utils.py.

# Then, import the three functions we defined in string_utils.py:

# Define a test class TestStringUtils that inherits from unittest.TestCase.
# Write test methods inside TestStringUtils to validate each imported function.
# Use assertion methods to test each function, including .assertEqual() and .assertTrue().

# Note: Make sure to use the if __name__ == '__main__' statement that uses unittest.main().

# Finally, run the unit tests with python3 test_string_utils.py. For the s string parameter, maybe try your name or favorite snack!