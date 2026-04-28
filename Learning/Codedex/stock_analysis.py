# Create a stock_analysis.py program that implements three functions:

# price_at(x) that finds the price on a given day x.
# max_price(a, b) that finds the maximum price from day a to day b.
# min_price(a, b) that finds the minimum price from day a to day b.
# The parameters of the days will be in the range of 1 to 20 (since that is the period for the stock we are analyzing).

# Make sure to call each function to test if your functions work correctly!

stock_prices = [34.68, 36.09, 34.94, 33.97, 34.68, 35.82, 43.41, 44.29, 44.65, 53.56, 49.85, 48.71, 48.71, 49.94, 48.53, 47.03, 46.59, 48.62, 44.21, 47.21]

def price_at(x):
    result = stock_prices[x-1]
    return result

def max_price(a, b):
    result = max(stock_prices[a-1:b])
    return result

def min_price(a, b):
    result = min(stock_prices[a-1:b])
    return result
    
print(price_at(6))
print(max_price(1, 20))
print(min_price(1, 20))
