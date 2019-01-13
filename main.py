import requests
from datetime import datetime, timedelta
import json
from googleapiclient.discovery import build
import googleapiclient.errors
from httplib2 import Http
from oauth2client import file, client, tools
import hashlib
import secrets
import config

class Gym:
    def __init__(self, id_number, address, shortname, target_calendar):
        self.id_number = id_number
        self.address = address
        self.shortname = shortname
        self.target_calendar = target_calendar

    def __repr__(self):
        return "{} ({}): {}".format(self.shortname, self.id_number, self.address)


goleta = Gym(1849, "Gold's Gym Goleta 6144 Calle Real Suite 101 Goleta CA 93117", "Goleta", secrets.goleta_calendar_id)
uptown = Gym(1848, "Gold's Gym Uptown 3908 State Street Santa Barbara CA 93105", "Uptown", secrets.uptown_calendar_id)
downtown = Gym(1847, "Gold's Gym Downtown 21 W. Carrillo Street Santa Barbara CA 93101", "Downtown", secrets.downtown_calendar_id)


def get_request_url(gym, day_offset=0):

    api_url_prefix = "https://www.goldsgym.com/api"
    date_format_string = "%Y-%m-%d"

    return "/".join([api_url_prefix,
                     "gyms",
                     str(gym.id_number),
                     "schedules",
                     "currentWeek?targetDate={}".format((datetime.now() + timedelta(days=day_offset)).strftime(date_format_string))])


def get_classes(gym, day_offset=0, retries=3):

    # Perform API request
    data = None
    url = get_request_url(gym, day_offset=day_offset)
    while data is None and retries > 0:
        try:
            start = datetime.now()
            data = requests.get(url=url).json()
            print("Request to {} completed in {} seconds".format(url, (datetime.now() - start).total_seconds()))
        except Exception as e:
            print("Request to {} failed with error: ".format(url, e))
            data = None
        finally:
            retries -= 1

    # Process received class list into our data structure
    classes = []
    if data is not None:
        for day in data.keys():
            for group_class in data[day]:
                classes.append(GroupClass(group_class, gym))
    else:
        print("Retries exceeded")

    return classes


class GroupClass:
    def __init__(self, json_string, gym):
        try:
            self.class_name = json_string["gym_class"]["name"]
            self.instructor_name = json_string["instructor"]["display_name"]
            self.start_time = datetime.strptime(json_string["next_occurrence"]["open"]["date"], "%Y-%m-%d %H:%M:%S.%f")
            self.end_time = datetime.strptime(json_string["next_occurrence"]["close"]["date"], "%Y-%m-%d %H:%M:%S.%f")
            self.duration = self.end_time - self.start_time
            self.gym = gym

            # Generate a unique ID that can be used for the event ID on the calendar
            class_id = json_string["class_id"]
            gym_id = json_string["gym_id"]
            instructor_id = json_string["instructor_id"]
            start_date_string = json_string["next_occurrence"]["open"]["date"]
            end_date_string = json_string["next_occurrence"]["close"]["date"]
            unique_id = str(class_id) + str(gym_id) + str(instructor_id) + start_date_string + end_date_string
            self.hash = hashlib.sha3_256(unique_id.encode('utf-8')).hexdigest()


        except Exception as e:
            self.class_name = ""
            self.instructor_name = ""
            self.start_time = None
            self.end_time = None
            self.duration = None
            print("Exception occurred while parsing JSON into class: {}".format(e))

    def __repr__(self):
        return "Class:      {}\n" \
               "Instructor: {}\n" \
               "Start Time: {}\n" \
               "End Time:   {}\n" \
               "Duration:   {}\n" \
               "Location:   {}".format(self.class_name,
                                         self.instructor_name,
                                         self.start_time,
                                         self.end_time,
                                         self.duration,
                                         self.gym
                                         )


# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/calendar'

def open_api():
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    return build('calendar', 'v3', http=creds.authorize(Http()))

def main():

    # Optionally load JSON from file
    # data = None
    # with open("response.txt", "r") as f:
    #     data = json.loads(f.read())

    group_classes = []

    for gym in [goleta, uptown, downtown]:
        if config.weeks_to_grab > 0:
            for num_weeks in range(0, config.weeks_to_grab):
                classes_to_add = get_classes(gym, day_offset=7*num_weeks)
                group_classes.extend(classes_to_add)
                print("{} classes loaded".format(len(classes_to_add)))
        else:
            ValueError("weeks_to_grab in config.py must be greater than 0!")

    # Filter group classes by what we want
    filtered_classes = [group_class for group_class in group_classes if group_class.class_name in config.class_filter]
    print("Total classes after filter: {}".format(len(filtered_classes)))

    # Call the Calendar API for event creation only on the desired classes from config.py
    service = open_api()
    for group_class in filtered_classes:

        # Create event data
        event = {
            'id': group_class.hash,
            'status': 'tentative',
            'summary': "{} with {}".format(group_class.class_name, group_class.instructor_name),
            'location': group_class.gym.address,
            'description': "{} with {}: {} minutes".format(group_class.class_name,
                                                           group_class.instructor_name,
                                                           int(group_class.duration.total_seconds() / 60)),
            'start': {
                'dateTime': group_class.start_time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                'timeZone': config.event_timezone,
            },
            'end': {
                'dateTime': group_class.end_time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                'timeZone': config.event_timezone,
            },
            'attendees': [{'email': email} for email in secrets.invite_addresses if type(email) == str],
            'reminders': {
                'useDefault': False,
                'overrides': [
                ],
            },
        }

        # Add a new or update an existing calendar event
        # Try-except needed because if event doesn't exist, the get() function returns a 400 error
        try:
            response = service.events().get(calendarId=group_class.gym.target_calendar, eventId=group_class.hash).execute()
            if response["status"] != "cancelled":
                # Update the existing event
                response = service.events().update(calendarId=group_class.gym.target_calendar, eventId=group_class.hash, body=event).execute()
                print('Event updated: %s' % (response.get('htmlLink')))
            else:
                # If event id cancelled, attempt to delete it and recreate it.
                # Anecdotal evidences says this DOES NOT work.
                response = service.events().delete(calendarId=group_class.gym.target_calendar, eventId=group_class.hash).execute()
                reponse = service.events().insert(calendarId=group_class.gym.target_calendar, body=event).execute()
                print('Event deleted and created: %s' % (response.get('htmlLink')))
        except googleapiclient.errors.HttpError:
            # Event doesn't exist - create it
            response = service.events().insert(calendarId=group_class.gym.target_calendar, body=event).execute()
            print('Event created: %s' % (response.get('htmlLink')))


if __name__ == '__main__':
    main()
