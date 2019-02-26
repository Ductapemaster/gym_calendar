from gym import Gym
from googleapiclient.discovery import build
import googleapiclient.errors
from google.oauth2 import service_account
import secrets
import config
import logging
from time import sleep

# TODO: Find a better location for logging instantiation - maybe another file
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)8s [ %(name)s ]: %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

logger_main = logging.getLogger('main')
logger_main.setLevel(logging.INFO)

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
                logger_main.info("{} classes loaded".format(len(gym.classes)))

                # Apply filter to get the classes we want
                filtered_classes = gym.filtered_classes(config.class_filter)
                logger_main.info("Total classes after filter: {}".format(len(filtered_classes)))
                selected_classes.extend(filtered_classes)

        else:
            ValueError("weeks_to_grab in config.py must be greater than 0!")

    # Call the Calendar API for event creation only on the desired classes from config.py
    service = open_api()
    for gym_class in selected_classes:

        # Delay to prevent rate limiting
        sleep(config.rate_limit_delay)

        # Create event data
        event = gym_class.event_object(attendees=secrets.invite_addresses)

        # Add a new or update an existing calendar event
        # Try-except needed because if event doesn't exist, the get() function returns a 400 error
        try:
            response = service.events().get(calendarId=gym_class.gym.target_calendar, eventId=gym_class.hash).execute()
            if response["status"] != "cancelled":
                # Update the existing event
                response = service.events().update(calendarId=gym_class.gym.target_calendar, eventId=gym_class.hash, body=event).execute()
                logger_main.info("Event updated: {}".format(response.get('htmlLink')))
            else:
                # If event id cancelled, attempt to delete it and recreate it.
                # Anecdotal evidences says this DOES NOT work.
                response = service.events().delete(calendarId=gym_class.gym.target_calendar, eventId=gym_class.hash).execute()
                reponse = service.events().insert(calendarId=gym_class.gym.target_calendar, body=event).execute()
                logger_main.info("Event deleted and created: {}".format(response.get('htmlLink')))
        except googleapiclient.errors.HttpError:
            # Event doesn't exist - create it
            response = service.events().insert(calendarId=gym_class.gym.target_calendar, body=event).execute()
            logger_main.info("Event created: {}".format(response.get('htmlLink')))


if __name__ == '__main__':
    main()
