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




