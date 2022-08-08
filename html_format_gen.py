import requests, json
import time
from datetime import datetime

data = {'client_id': 1020,
      'client_secret': 'e7b829ed7dbf7d70e980c1fbbd85b9c9',
      'grant_type': 'client_credentials'}

responseJSON = requests.post('https://iit.libcal.com/1.1/oauth/token',data=data, stream=True)

response = responseJSON.json()
key = 'Bearer ' + response['access_token']
header = {'Authorization': key}

# returns a list of bookings with:
# simplified time format
# past bookings removed
# back to back listings combined
def bookings_list():

    bookingsJSON = requests.get('https://iit.libcal.com/1.1/space/bookings?eid=116094', headers=header)
    bookings = bookingsJSON.json()

    # UNCOMMENT TO SAVE BOOKINGS JSON TO FILE
    bookingsfile = bookingsJSON.json()
    with open('data.json', 'w') as file:
        json.dump(bookingsfile, file)

    cleaned_bookings = []
    for booking in bookings:
        if booking["status"] == "Confirmed":
            cleaned_booking = [time_24hr(booking["fromDate"]), time_24hr(booking["toDate"])]
            cleaned_bookings.append(cleaned_booking)

    def delete_past_bookings():
        i = 0
        length = len(cleaned_bookings)
        while i < length:
            if time_to_int(cleaned_bookings[i][1]) <= time_to_int(current_time):
                del(cleaned_bookings[i])
                length -= 1
            else:
                i += 1
    
    def combine_b2b_bookings():
        i = 0
        length = len(cleaned_bookings)-1
        while i < length:
            if cleaned_bookings[i][1] == cleaned_bookings[i+1][0]:
                cleaned_bookings[i][1] = cleaned_bookings[i+1][1]
                del(cleaned_bookings[i+1])
                length -= 1
            else:
                i += 1

    delete_past_bookings()
    combine_b2b_bookings()

    return cleaned_bookings

# converts a 24hr time (ex. 13:37) to mins since 0:00 (ex. 817) for easy math
def time_to_int(time24hr):
    hours = int(time24hr[0:2])
    mins = int(time24hr[3:5])
    
    #time in mins
    total_time = (hours * 60) + mins
    return total_time

# converts the messy time format from the libcal API (ex. 2022-07-22T14:15:00-05:00) to a 24hr format (14:15)
def time_24hr(time):
    return time[11:16]

# converts 24hr (ex. 13:37) time to 12hr time with am/pm (1:37 pm)
def time_12hr(time):
    hours = int(time[0:2])
    ampm = " AM"

    if hours >= 12:
        ampm = " PM"
    if hours > 12:
         hours -= 12
    
    return (str(hours) + ":" + time[3:5] + ampm)

# this function will return a dictionary with all the formattings for the html
def html_format():
    spacesJSON = requests.get('https://iit.libcal.com/1.1/space/item/116094?availability', headers=header)
    spaces = spacesJSON.json()

    now = datetime.now()
    global current_time
    current_time = now.strftime("%H:%M")

    # UNCOMMENT TO SAVE SPACES JSON TO FILE
    # testfile = spacesJSON.json()
    # with open('data.json', 'w') as f:
    #     json.dump(testfile, f)

    bookings = bookings_list()
    open_time = time_24hr(spaces[0]["availability"][0]["from"])
    closed_time = time_24hr(spaces[0]["availability"][-1]["to"])

    html_format = {"bg_color":              "#585191", # purple
                   "space_name":            spaces[0]["name"],
                   "availability_message":  "error",
    }
    print(current_time, ": current bookings:", bookings)

    # checks if there is a booking happening rn
    def check_unavailable(bookings_list):
        start_time = time_to_int(bookings_list[0][0])
        end_time = time_to_int(bookings_list[0][1])
        int_current_time = time_to_int(current_time)

        return (start_time <= int_current_time) and (int_current_time < end_time)

    # if the current time is past closing time
    if time_to_int(current_time) > time_to_int(closed_time):
        html_format["bg_color"] =             "#C1292E" # red
        html_format["availability_message"] = "closed right now! it is past closing time " + time_12hr(closed_time) 
    # if there are no bookings rn
    elif bookings == []:
        html_format["bg_color"] =             "#119822" # green
        html_format["availability_message"] = "available to " + time_12hr(closed_time)
    # if the current time is in the middle of a booking
    elif check_unavailable(bookings):
        html_format["bg_color"] =             "#C1292E" # red
        html_format["availability_message"] = "in use to " + time_12hr(bookings[0][1])
    # if the current time is before opening time
    elif time_to_int(current_time) < time_to_int(open_time):
        html_format["bg_color"] =             "#C1292E" # red
        html_format["availability_message"] = "closed right now! come back at " + time_12hr(open_time)
    # if there is no booking rn, but there is one coming up
    else:
        html_format["bg_color"] =             "#119822" # green
        html_format["availability_message"] = "available to " + time_12hr(bookings[0][0])
    
    return html_format

while True:
    # to open/create a new file in the write mode
    f = open('html_format.js', 'w')

    html_format_js = "var html_format = " + str(html_format())

    # writing the code into the file
    f.write(html_format_js)
    
    time.sleep(45)

