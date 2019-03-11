import logging
from datetime import datetime, timedelta
from hashlib import sha3_256
import config

logger_gym_class = logging.getLogger("gym_class")


# TODO: split into a parent class that doesn't include the calendar event specific code and a child that does
class GymClass:
    def __init__(self, class_name="",
                 instructor_name="",
                 start_time=datetime.now(),
                 end_time=datetime.now(),
                 gym=None,
                 id_seed=" ",
                 start_time_buffer=0,
                 end_time_buffer=0):
        """
        Create instance of a GymClass
        :param class_name: String, name of gym class
        :param instructor_name: String, name of instructor
        :param start_time: Datetime oject representing the start of the class
        :param end_time: Datetime oject representing the end of the class
        :param gym: Gym object that the particular class is physically at
        :param id_seed: Seed for the hash function to generate a unique ID (used for identifying the calendar events)
        :param start_time_buffer: Minutes to move the calendar event start time backward (for travel time, etc)
        :param end_time_buffer: Minutes to move the calendar event's end time forward (for travel time, etc)
        """
        self.class_name = class_name
        self.instructor_name = instructor_name

        self.class_start_time = start_time
        self.class_end_time = end_time
        self.duration = self.class_end_time - self.class_start_time

        self._start_time_buffer = timedelta(minutes=end_time_buffer)
        self._end_time_buffer = timedelta(minutes=start_time_buffer)

        self.gym = gym
        self.hash = sha3_256(id_seed.encode('utf-8')).hexdigest()

    @classmethod
    def from_json(cls, gym, json_string):
        """
        Build an instance of our class from the JSON response from the Gold's Gym API
        :param gym: Object instance to the gym the class is at
        :param json_string: API response string
        :return: Instance of the GymClass class
        """
        try:
            class_name = json_string["gym_class"]["name"]
            instructor_name = json_string["instructor"]["display_name"]
            start_time = datetime.strptime(json_string["next_occurrence"]["open"]["date"], "%Y-%m-%d %H:%M:%S.%f")
            end_time = datetime.strptime(json_string["next_occurrence"]["close"]["date"], "%Y-%m-%d %H:%M:%S.%f")

            # Generate a unique ID that can be used for the event ID on the calendar
            class_id = json_string["class_id"]
            gym_id = json_string["gym_id"]
            instructor_id = json_string["instructor_id"]
            start_date_string = json_string["next_occurrence"]["open"]["date"]
            end_date_string = json_string["next_occurrence"]["close"]["date"]
            unique_id = str(class_id) + str(gym_id) + str(instructor_id) + start_date_string + end_date_string

        except Exception:
            class_name = ""
            instructor_name = ""
            start_time = datetime.now()
            end_time = datetime.now()
            unique_id = " "
            logger_gym_class.error("Error parsing JSON into class", exc_info=True)

        return cls(class_name=class_name,
                   instructor_name=instructor_name,
                   start_time=start_time,
                   end_time=end_time,
                   gym=gym,
                   id_seed=unique_id)

    @property
    def start_time_buffer(self):
        return self._start_time_buffer.min

    @start_time_buffer.setter
    def start_time_buffer(self, buffer):
        """
        We store our buffer time object internally as a timedelta object, so this provides a setter method for a numeric argument
        :param buffer: Buffer time in minutes to add to beginning of the class
        :return:
        """
        if buffer < 0:
            logger_gym_class.warning("Start time buffer value should be a positive value. Continuing with supplied value {}".format(buffer))
        self._start_time_buffer = timedelta(minutes=buffer)

    @property
    def end_time_buffer(self):
        return self._end_time_buffer.min

    @end_time_buffer.setter
    def end_time_buffer(self, buffer):
        """
        We store our buffer time object internally as a timedelta object, so this provides a setter method for a numeric argument
        :param buffer: Buffer time in minutes to add to end of the class
        :return:
        """
        if buffer < 0:
            logger_gym_class.warning("End time buffer value should be a positive value. Continuing with supplied value {}".format(buffer))
        self._end_time_buffer = timedelta(minutes=buffer)

    def event_object(self, attendees=[]):
        """
        Provide a JSON string for creating a Google Calendar event
        :param attendees: List of email addressed to include in the event
        :return: JSON string to parameterize calendar event
        """
        return {
            'id': self.hash,
            'status': 'tentative',
            'summary': "{} with {}".format(self.class_name, self.instructor_name),
            'location': self.gym.address,
            'description': "{} with {}: {} minutes".format(self.class_name,
                                                           self.instructor_name,
                                                           int(self.duration.total_seconds() / 60)),
            'start': {
                'dateTime': (self.class_start_time - self._start_time_buffer).strftime("%Y-%m-%dT%H:%M:%S%z"),
                'timeZone': config.event_timezone,
            },
            'end': {
                'dateTime': (self.class_end_time + self._end_time_buffer).strftime("%Y-%m-%dT%H:%M:%S%z"),
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
                                       self.class_start_time,
                                       self.class_end_time,
                                       self.duration,
                                       self.gym
                                       )
