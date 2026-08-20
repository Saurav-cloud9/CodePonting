import random

def play():
    symbols = ['🍒','🍇','🍉','7️⃣']
    results = random.choices(symbols, k=3)
    print(' |'.join(results))
    if results[0] == '7️⃣' and results[1] == '7️⃣' and results[2] == '7️⃣':
        print("Jackpot! 💰")
    else:
        print("Thanks for playing!")

while True:
    play()
    user_input = input("Do you want to play again? (Y/N): ").lower()
    if user_input == 'y':
        continue        
    else:
        break
    
print("Thanks for playing!")