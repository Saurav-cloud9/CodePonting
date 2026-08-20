# ─────────────────────────────────────────────
# ⚽ Real Madrid — UEFA Champions League 2024
# Data Analyst Task Brief
# ─────────────────────────────────────────────

# As a data analyst for Real Madrid, the UEFA Champions
# League 2024 champions, you've been given a dataset
# containing player info and match statistics.

# Let's start analyzing!

# ✅ Task 1: Create a list of dictionaries where each
#    dictionary represents a player. Include attributes
#    such as 'name', 'position', and 'jersey_number'.

# ✅ Task 2: Print out a list of all unique player
#    positions in the dataset.

# ✅ Task 3: Choose a player and update their match
#    statistics in the dataset.

# ✅ Task 4: Calculate the average statistics
#    (e.g., goals, assists, pass_accuracy) for all
#    players and print the results.

players = [
    {"name": "Thibaut Courtois", "position": "Goalkeeper",  "jersey": 1,  "goals": 0, "assists": 0, "pass_accuracy": 72.5},
    {"name": "Dani Carvajal",    "position": "Defender",    "jersey": 2,  "goals": 2, "assists": 3, "pass_accuracy": 84.1},
    {"name": "Eder Militao",     "position": "Defender",    "jersey": 3,  "goals": 1, "assists": 0, "pass_accuracy": 88.3},
    {"name": "David Alaba",      "position": "Defender",    "jersey": 4,  "goals": 0, "assists": 1, "pass_accuracy": 87.6},
    {"name": "Jude Bellingham",  "position": "Midfielder",  "jersey": 5,  "goals": 8, "assists": 5, "pass_accuracy": 83.2},
    {"name": "Nacho Fernandez",  "position": "Defender",    "jersey": 6,  "goals": 1, "assists": 0, "pass_accuracy": 86.0},
    {"name": "Vinicius Jr",      "position": "Forward",     "jersey": 7,  "goals": 6, "assists": 4, "pass_accuracy": 78.9},
    {"name": "Toni Kroos",       "position": "Midfielder",  "jersey": 8,  "goals": 2, "assists": 7, "pass_accuracy": 91.4},
    {"name": "Joselu",           "position": "Forward",     "jersey": 9,  "goals": 4, "assists": 1, "pass_accuracy": 70.2},
    {"name": "Luka Modric",      "position": "Midfielder",  "jersey": 10, "goals": 1, "assists": 4, "pass_accuracy": 89.7},
    {"name": "Rodrygo",          "position": "Forward",     "jersey": 11, "goals": 5, "assists": 3, "pass_accuracy": 79.5},
]

positions = []
for p in players:
    positions.append(p["position"])

print(list(set(positions)))


for p in players:
    if p['name'] == 'Toni Kroos':
        p['match_goals'] = 0
        p['match_assists'] = 1
        p['match_total_shots'] = 2

print(players[7])

sum_goals = 0
sum_assists = 0
sum_pass_accuracy = 0
for p in players:
    sum_goals += p['goals']
    sum_assists += p['assists']
    sum_pass_accuracy += p['pass_accuracy']

print(f"Avg goals: {sum_goals/11:.2f}")
print(f"Avg_assists: {sum_assists/11:.2f}")
print(f"Avg_pass_accuracy: {sum_pass_accuracy/11:.2f}")
