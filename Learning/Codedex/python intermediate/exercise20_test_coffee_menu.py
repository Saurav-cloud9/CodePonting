# Then, let's define a test class and write some tests:

# Create and save the test_coffee_menu.py file with the TestCoffeeMenu class.
# Write descriptive unit test using assertions (ex. test_get_price_existing_item(), test_get_price_non_existing_item(), test_add_item())
# After running the tests, observe the output to see if all tests pass successfully.

import unittest
from exercise20_coffee_menu import CoffeeMenu

class TestCoffeeMenu(unittest.TestCase):
    def setUp(self):
        self.order = CoffeeMenu()

    def tearDown(self):
        self.order = None

    def test_get_price_existing_item(self):
        self.assertEqual(self.order.menu['espresso'], 2.50)
    
    def test_get_price_non_existing_item(self):
        with self.assertRaises(KeyError):
            self.order.menu['tea']

    def test_add_item(self):
        self.order.menu['irish_tea'] = 3.50
        self.assertIn('irish_tea', self.order.menu)

if __name__ == '__main__':
    unittest.main()



