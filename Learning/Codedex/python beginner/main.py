import datetime
import bday_messages

today = datetime.date.today()
next_birthday = datetime.date(2027, 4, 16)

days_away = (next_birthday - today).days

if today == next_birthday:
    print(bday_messages.random_message)
else:
    print(f"My next birthday is {days_away} days away")