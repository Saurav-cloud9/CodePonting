# Instructions
# We’ve all sent a message we knew we shouldn’t. 🫣

# Thankfully, technology is here to save the day! 🌟

# Let's use .seek() and .truncate() to simulate unsending a message within a text file.

# First, create a new sent_message.txt file and write a secret message to it:

# sent_message = 'Hey there! This is a secret message.'

# with open('sent_message.txt', 'w') as file:
#   file.write(sent_message)

# Read the message and use .seek() to move the cursor to the beginning (0):

# with open('sent_message.txt', 'r+') as file:
#   # Read the sent message from the file
#   original_message = file.read()
      
#   # Move the cursor to the beginning of the file
#   file.seek(0)

# Note: r+ in the open() function is used to indicate both reading and writing are allowed in the file.

# # Modify the message to simulate unsending
# unsent_message = 'This message has been unsent.'

# Use .truncate() to reset the content to the length of the unsend message.
# Save the new message to the file.
# Print your messages!
# Note: seek(0) is used to move the cursor to the beginning of the file before modifying the message.

# Then, truncate() is used to adjust the file size to match the length of the new message. This simulates the act of unsending the message within the file.

import os
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, 'sent_message.txt')

try:
    file = open(file_path, 'w') # file opened in write mode
    file.write("here is a secret, and the secret is here") # file written via write func
finally:
    file.close() #file is closed

try:
    file = open(file_path, 'r+') # file opened in read/write mode
    original_message = file.read() # file read via read func
    print(original_message) #file is printed
    part2_message = file.read() # file is read again
    print(part2_message) # file is printed but nothing shows here in print coz the cursor was already past the last character of the original message

    file.seek(0) # the cursor is moved to the begining
    part3_message = file.read() # file is read from the begining since the cursor is now at the start
    print(part3_message) # the file was read and stored in another variable which is printed

    file.seek(0) # cursor moved back to the beginning of the file

    unsent_message = 'This message has been unsent.'

    file.write(unsent_message)

    file.seek(0)

    file.truncate(len(unsent_message))


    # file.truncate(4) # everything after the first 4 characters is deleted or truncated via the truncate func but the cursor remains at position 0
    part4_message = file.read() # the left over chars i.e. the first 4 chars are read via read func and stored inside a variable
    print(part4_message) # the variable from line 64 is now printed, the output shows the first 4 chars 


finally:
    file.close() # the file is finally closed via finally clause -> close func