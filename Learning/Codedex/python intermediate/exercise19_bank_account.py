# Instructions
# Ever felt like your bank account balance magically changed from one day to another?

# Let's become our own wealth manager! Let's build a test to ensuring our BankAccount class behaves better than our real bank account! We'll validate deposits, withdrawals, and balance checks.

# We will be writing test cases to validate the behavior of the BankAccount class for deposit and withdrawal operations.

# Create a BankAccount
# Create a new bank_account.py file and define a BankAccount class with deposit and withdraw functionalities:

class BankAccount:
  def __init__(self, initial_balance=0):
    self.balance = initial_balance

  def deposit(self, amount):
    if amount <= 0:
      raise ValueError('Deposit amount must be positive')
    self.balance += amount

  def withdraw(self, amount):
    if amount <= 0:
      raise ValueError('Withdrawal amount must be positive')
    if amount > self.balance:
      raise ValueError('Insufficient funds')
    self.balance -= amount

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


