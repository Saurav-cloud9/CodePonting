import random

print("===================\nRock Paper Scissors\n===================")
print("1) ✊\n2) ✋\n3) ✌️\n4) 🦎\n5) 🖖")
player = int(input("Pick a number: "))
computer = random.randint(1, 5)
player_choice = ''
computer_choice = ''

if player == 1:
    player_choice = '✊'
elif player == 2:
    player_choice = '✋'
elif player == 3:
    player_choice = '✌️'
elif player == 4:
    player_choice = '🦎'
else:
    player_choice = '🖖'
    
if computer == 1:
    computer_choice = '✊'
elif computer == 2:
    computer_choice = '✋'
elif computer == 3:
    computer_choice = '✌️'
elif computer == 4:
    computer_choice = '🦎'
else:
    computer_choice = '🖖'

print(f"You chose: {player_choice}")
print(f"CPU chose: {computer_choice}")

if player == 1 and computer == 3:
    print("The player won")
elif player == 2  and computer == 3:
    print("The CPU won")
elif player == 2  and computer == 1:
    print("The player won")
elif player == 1 and computer == 2:
    print("The CPU won")
elif player == 3 and computer == 1:
    print("The CPU won")
elif player == 3 and computer == 2:
    print("The player won")
elif player == 1  and computer == 4:
    print("The player won")
elif player == 4  and computer == 1:
    print("The CPU won")
elif player == 4  and computer == 5:
    print("The player won")
elif player == 5  and computer == 4:
    print("The CPU won")
elif player == 5  and computer == 3:
    print("The player won")
elif player == 3  and computer == 5:
    print("The CPU won")
elif player == 3  and computer == 4:
    print("The player won")
elif player == 4  and computer == 3:
    print("The CPU won")
elif player == 4  and computer == 2:
    print("The player won")
elif player == 2  and computer == 4:
    print("The CPU won")
elif player == 2  and computer == 5:
    print("The player won")
elif player == 5  and computer == 2:
    print("The CPU won")
elif player == 5  and computer == 1:
    print("The player won")
elif player == 1  and computer == 5:
    print("The CPU won")
else:
    print("Its a tie")


