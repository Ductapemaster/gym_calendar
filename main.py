import requests
from datetime import datetime, timedelta
from googleapiclient.discovery import build
import googleapiclient.errors
from google.oauth2 import service_account
import hashlib
import secrets
import config
import logging
from time import sleep

# TODO: Find a better location for logging instantiation - maybe another file
logger_main = logging.getLogger('main')
logger_google_api = logging.getLogger('googleapiclient')
logger_urllib3 = logging.getLogger('urllib3')

logger_main.setLevel(logging.INFO)
logger_google_api.setLevel(logging.ERROR)
logger_urllib3.setLevel(logging.ERROR)

formatter = logging.Formatter('%(asctime)s %(levelname)8s [ %(name)s ]: %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

logger_main.addHandler(stream_handler)
logger_google_api.addHandler(stream_handler)
logger_urllib3.addHandler(stream_handler)


class Gym:
    def __init__(self, id_number, address, shortname, target_calendar="primary"):
        self.id_number = id_number
        self.address = address
        self.shortname = shortname
        self.target_calendar = target_calendar
        logger_main.debug("Create instance of Gym object: {}".format(self.__repr__()))

    def __repr__(self):
        return "{} ({}): {}".format(self.shortname, self.id_number, self.address)


def get_request_url(gym, day_offset=0):

    api_url_prefix = "https://www.goldsgym.com/api"
    date_format_string = "%Y-%m-%d"
    url = "/".join([api_url_prefix,
                     "gyms",
                     str(gym.id_number),
                     "schedules",
                     "currentWeek?targetDate={}".format((datetime.now() + timedelta(days=day_offset)).strftime(date_format_string))])

    logger_main.debug('Generated Gym API URL: {}'.format(url))
    return url


def get_classes(gym, day_offset=0, retries=3):

    # Perform API requests
    data = None
    url = get_request_url(gym, day_offset=day_offset)
    while data is None and retries > 0:
        try:
            data = requests.get(url=url).json()
            logger_main.info("Request to {} completed".format(url))
        except Exception as e:
            logger_main.error("Request to {} FAILED".format(url))
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
        logger_main.error("Retries for url {} exceeded - forfeiting".format(url))

    logger_main.debug("{} classes retrieved from url {}".format(len(classes), url))
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
            logging.error("Error parsing JSON into class", exc_info=True)

    def event_object(self, attendees=[]):
        return {
            'id': self.hash,
            'status': 'tentative',
            'summary': "{} with {}".format(self.class_name, self.instructor_name),
            'location': self.gym.address,
            'description': "{} with {}: {} minutes".format(self.class_name,
                                                           self.instructor_name,
                                                           int(self.duration.total_seconds() / 60)),
            'start': {
                'dateTime': self.start_time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                'timeZone': config.event_timezone,
            },
            'end': {
                'dateTime': self.end_time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                'timeZone': config.event_timezone,
            },
            'attendees': [{'email': email} for email in attendees if type(email) == str],
            'reminders': {
                'useDefault': False,
                'overrides': [
                ],
            },
        }

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


SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'service.json'


def open_api():
    logger_main.debug("Attempting to open API")
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    logger_main.debug("Using credentials file {}".format(SERVICE_ACCOUNT_FILE))
    if not credentials:
        logger_main.error("Invalid credentials!")
        exit(-1)
    logger_main.debug("Open API success!")
    return build('calendar', 'v3', credentials=credentials)


def main():

    # Optionally load JSON from file
    # data = None
    # with open("response.txt", "r") as f:
    #     data = json.loads(f.read())

    group_classes = []

    # Read in gyms from config and appropriate target calendars from secrets
    gyms = [Gym(**gym) for gym in config.gyms]

    for gym in gyms:
        if config.weeks_to_grab > 0:

            # Set up target calendar if prescribed in secrets.py
            if gym.id_number in secrets.calendar_mapping:
                gym.target_calendar = secrets.calendar_mapping[gym.id_number]

            # Go query the API
            for num_weeks in range(0, config.weeks_to_grab):
                classes_to_add = get_classes(gym, day_offset=7*num_weeks)
                group_classes.extend(classes_to_add)
                logger_main.info("{} classes loaded".format(len(classes_to_add)))
        else:
            ValueError("weeks_to_grab in config.py must be greater than 0!")

    # Filter group classes by what we want
    filtered_classes = [group_class for group_class in group_classes if group_class.class_name in config.class_filter]
    logger_main.info("Total classes after filter: {}".format(len(filtered_classes)))

    # Call the Calendar API for event creation only on the desired classes from config.py
    service = open_api()
    for group_class in filtered_classes:

        # Delay to prevent rate limiting
        sleep(config.rate_limit_delay)

        # Create event data
        event = group_class.event_object(attendees=secrets.invite_addresses)

        # Add a new or update an existing calendar event
        # Try-except needed because if event doesn't exist, the get() function returns a 400 error
        try:
            response = service.events().get(calendarId=group_class.gym.target_calendar, eventId=group_class.hash).execute()
            if response["status"] != "cancelled":
                # Update the existing event
                response = service.events().update(calendarId=group_class.gym.target_calendar, eventId=group_class.hash, body=event).execute()
                logger_main.info("Event updated: {}".format(response.get('htmlLink')))
            else:
                # If event id cancelled, attempt to delete it and recreate it.
                # Anecdotal evidences says this DOES NOT work.
                response = service.events().delete(calendarId=group_class.gym.target_calendar, eventId=group_class.hash).execute()
                reponse = service.events().insert(calendarId=group_class.gym.target_calendar, body=event).execute()
                logger_main.info("Event deleted and created: {}".format(response.get('htmlLink')))
        except googleapiclient.errors.HttpError:
            # Event doesn't exist - create it
            response = service.events().insert(calendarId=group_class.gym.target_calendar, body=event).execute()
            logger_main.info("Event created: {}".format(response.get('htmlLink')))


if __name__ == '__main__':
    main()
