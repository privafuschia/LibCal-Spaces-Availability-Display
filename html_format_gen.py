import requests, json
import time
from datetime import datetime
import logging

data = {'client_id': 1020,
      'client_secret': 'e7b829ed7dbf7d70e980c1fbbd85b9c9',
      'grant_type': 'client_credentials'}

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
def time_12hr(time24hr):
    hours = int(time24hr[0:2])
    ampm = " AM"

    if hours >= 12:
        ampm = " PM"
    if hours > 12:
         hours -= 12
    
    return (str(hours) + ":" + time24hr[3:5] + ampm)

# returns a list of bookings with:
# simplified time format
# past bookings removed
# back to back listings combined
def bookings_list():

    bookingsJSON = requests.get('https://iit.libcal.com/1.1/space/bookings?eid=104617', headers=header)
    bookings = bookingsJSON.json()

    # saves json file containing all bookings in the day (FOR TROUBLESHOOTING)
    bookingsfile = bookingsJSON.json()
    with open('bookings.json', 'w') as file:
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
            if time_to_int(cleaned_bookings[i][1]) <= current_time:
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

# this function will return a dictionary with all the formattings for the html
def html_format():
    spacesJSON = requests.get('https://iit.libcal.com/1.1/space/item/104617?availability', headers=header)
    spaces = spacesJSON.json()

    # saves json file containing all available time blocks in the day (FOR TROUBLESHOOTING)
    spacesfile = spacesJSON.json()
    with open('spaces.json', 'w') as f:
        json.dump(spacesfile, f)

    global bookings
    bookings = bookings_list()

    # opening and closing times for logic and messaging
    if spaces[0]["availability"] != []:
        next_open_time = time_24hr(spaces[0]["availability"][0]["from"])
        global closed_time
        closed_time = time_24hr(spaces[0]["availability"][-1]["to"])

    html_format = {"bg_color":              "#585191", # purple
                   "space_name":            spaces[0]["name"],
                   "availability_message":  "error",
    }
    # if all time slots are booked
    if (spaces[0]["availability"] == []) and (bookings != []):
        html_format["bg_color"] =             "#C1292E" # red
        html_format["availability_message"] = "booked for the day"
    # if it is past closing time (inserts closing time if it exists)
    elif spaces[0]["availability"] == []:
        html_format["bg_color"] =             "#C1292E" # red
        html_format["availability_message"] = "closed" + (" @ " + time_12hr(closed_time) if ("closed_time" in globals()) else "")
    # if the current time is before opening time
    elif current_time < time_to_int(next_open_time):
        html_format["bg_color"] =             "#C1292E" # red
        html_format["availability_message"] = "available at " + time_12hr(next_open_time)
    # if there are no bookings rn
    elif bookings == []:
        html_format["bg_color"] =             "#119822" # green
        html_format["availability_message"] = "available to " + time_12hr(closed_time)
    # if there is no booking rn, but there is one coming up
    else:
        html_format["bg_color"] =             "#119822" # green
        html_format["availability_message"] = "available to " + time_12hr(bookings[0][0])
    
    return html_format

print("running!")
logging.basicConfig(filename="libcal_display.log", level=logging.INFO)
logging.info("<-- NEW SESSION -->")
# looping logic to keep html page with information up to date
while True:
    now = datetime.now()
    global current_time
    current_time = time_to_int(now.strftime("%H:%M"))

    # generates assess key
    responseJSON = requests.post('https://iit.libcal.com/1.1/oauth/token',data=data, stream=True)
    response = responseJSON.json()
    key = 'Bearer ' + response['access_token']
    header = {'Authorization': key}

    # creates/updates html_format.js file containing information for the html page
    html_format_file = open('html_format.js', 'w')
    html_format_data = str(html_format())
    html_format_js = "var html_format = " + html_format_data
    html_format_file.write(html_format_js)
    html_format_file.close()

    # LOGGING
    logging.info(str(datetime.now()) + " - bookings: " + str(bookings) + " - display data: " + html_format_data)

    time.sleep(60)

