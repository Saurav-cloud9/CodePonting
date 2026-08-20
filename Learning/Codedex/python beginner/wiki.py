import wikipedia

query = "Sachin Tendulkar"

result = wikipedia.summary(query, sentences=2)

print(result)