import os
import datetime
import time


# Checks the extension of a given file
# file_name: name of file with extension
# extensions: list of allowed extensions
def check_extension(file_name, extensions):
    length = len(file_name)
    lowercase = file_name.lower()

    # If the string length is less than 3 character, it has no extension
    if length < 3:
        return False
    else:
        for extension in extensions:
            found = lowercase.find(extension, length - 4, length)

            # Extension found, return true
            if found != -1:
                return True
    # Extension not found, return false
    return False


# Writes a message to the console with a timestamp
# message: Message to write to the console
def write_message(message):
    time_sec = time.time()
    timestamp = datetime.datetime.fromtimestamp(time_sec).strftime('%Y-%m-%d %H:%M:%S')

    message = "[" + str(timestamp) + "] " + str(message)

    print(message)




