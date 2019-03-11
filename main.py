from gym import Gym
from googleapiclient.discovery import build
import googleapiclient.errors
from google.oauth2 import service_account
import secrets
import config
import logging
from time import sleep
from os import path

# TODO: Find a better location for logging instantiation - maybe another file
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)8s [ %(name)s ]: %(message)s')

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.INFO)

log_file_full_path = '/'.join([config.log_base_path, config.log_file_name])
if not path.exists(log_file_full_path):
    with open(log_file_full_path, 'a'):
        pass

file_handler = logging.FileHandler(log_file_full_path)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

logger.addHandler(stream_handler)
logger.addHandler(file_handler)

logger_main = logging.getLogger('main')

logger_google_api = logging.getLogger('googleapiclient')
logger_google_api.setLevel(logging.ERROR)


def open_api():
    scopes = ['https://www.googleapis.com/auth/calendar']
    service_account_file = 'service.json'

    logger_main.debug("Attempting to open API")
    credentials = service_account.Credentials.from_service_account_file(
        service_account_file, scopes=scopes)
    logger_main.debug("Using credentials file {}".format(service_account_file))

    if not credentials:
        logger_main.error("Invalid credentials!")
        exit(-1)
    logger_main.debug("Open API success!")

    return build('calendar', 'v3', credentials=credentials)


def main():

    logger_main.info('Gold\'s Gym Calendar updater script started')

    # Optionally load JSON from file
    # data = None
    # with open("response.txt", "r") as f:
    #     data = json.loads(f.read())

    selected_classes = []

    # Read in gyms from config and appropriate target calendars from secrets
    gyms = [Gym(**gym) for gym in config.gyms]

    for gym in gyms:
        if config.weeks_to_grab > 0:

            # Set up target calendar if prescribed in secrets.py
            if gym.id_number in secrets.calendar_mapping:
                gym.target_calendar = secrets.calendar_mapping[gym.id_number]

            # Go query the API
            for num_weeks in range(0, config.weeks_to_grab):
                gym.query_classes(day_offset=7 * num_weeks)
                logger_main.debug("{} classes loaded".format(len(gym.classes)))

                # Apply filter to get the classes we want
                filtered_classes = gym.filtered_classes(config.class_filter)
                logger_main.debug("Total classes after filter: {}".format(len(filtered_classes)))
                selected_classes.extend(filtered_classes)

        else:
            ValueError("weeks_to_grab in config.py must be greater than 0!")

    # Call the Calendar API for event creation only on the desired classes from config.py
    service = open_api()
    logger_main.info('{} classes to add'.format(len(selected_classes)))
    events_updated = 0
    events_created = 0
    for gym_class in selected_classes:

        # Delay to prevent rate limiting
        sleep(config.rate_limit_delay)

        # Create event data
        gym_class.start_time_buffer = config.event_start_time_buffer
        gym_class.end_time_buffer = config.event_end_time_buffer
        event = gym_class.event_object(attendees=secrets.invite_addresses)

        # Add a new or update an existing calendar event
        # Try-except needed because if event doesn't exist, the get() function returns a 400 error
        try:
            response = service.events().get(calendarId=gym_class.gym.target_calendar, eventId=gym_class.hash).execute()
            if response["status"] != "cancelled":
                # Update the existing event
                response = service.events().update(calendarId=gym_class.gym.target_calendar, eventId=gym_class.hash, body=event).execute()
                logger_main.debug("Event updated: {}".format(response.get('htmlLink')))
            else:
                # If event id cancelled, attempt to delete it and recreate it.
                # Anecdotal evidences says this DOES NOT work.
                response = service.events().delete(calendarId=gym_class.gym.target_calendar, eventId=gym_class.hash).execute()
                reponse = service.events().insert(calendarId=gym_class.gym.target_calendar, body=event).execute()
                logger_main.debug("Event deleted and created: {}".format(response.get('htmlLink')))
            events_updated += 1
        except googleapiclient.errors.HttpError:
            # Event doesn't exist - create it
            response = service.events().insert(calendarId=gym_class.gym.target_calendar, body=event).execute()
            logger_main.debug("Event created: {}".format(response.get('htmlLink')))
            events_created += 1

    logger_main.info('Calendar updates complete: {} events created, {} updated'.format(events_created, events_updated))


if __name__ == '__main__':
    main()
