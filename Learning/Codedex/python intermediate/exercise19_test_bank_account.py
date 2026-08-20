# Set up your BankAccount
# Create a BankAccount instance with an initial balance of 100.

# Test Initial Balance
# Create a test_bank_account.py file and define a TestBankAccount() class.

# Write a test method (test_initial_balance) to verify that the initial balance is set correctly to 100.
# Inside this test file, define the following:

# A setUp() method to make a new BankAccount object called account, with an initial balance of 100.
# A tearDown() method that sets the value of a BankAccount object to None.
# Test Bank Operations
# Write the following tests that check for a correct balance:
# A test_deposit_positive_amount() method that adds 50 and confirms the new balance is 150.
# Define another set of tests all meant to raise a ValueError:

# A test_deposit_zero_amount() method for if we try to deposit 0.
# Save the file and run the tests from your terminal to validate the behavior of the BankAccount class.

from exercise19_bank_account import BankAccount
import unittest

class TestBankAccount(unittest.TestCase):
    def setUp(self):
        self.account = BankAccount(100)

    def tearDown(self):
        self.account = None
    
    def test_initial_balance(self):
        self.assertEqual(self.account.balance, 100)

    def test_deposit_positive_amount(self):
        self.account.deposit(50)
        self.assertEqual(self.account.balance, 150)

    def test_deposit_zero_amount(self):
        with self.assertRaises(ValueError):
            self.account.deposit(0)

if __name__ == '__main__':
    unittest.main()
