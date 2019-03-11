import logging
from datetime import datetime, timedelta
from hashlib import sha3_256
import config

logger_gym_class = logging.getLogger("gym_class")


# TODO: split into a parent class that doesn't include the calendar event specific code and a child that does
class GymClass:
    def __init__(self, class_name="", instructor_name="",
                 start_time=datetime.now(), end_time=datetime.now(),
                 gym=None, id_seed=" "):
        self.class_name = class_name
        self.instructor_name = instructor_name
        self.start_time = start_time
        self.end_time = end_time
        self.duration = self.end_time - self.start_time
        self.gym = gym
        self.hash = sha3_256(id_seed.encode('utf-8')).hexdigest()

    @classmethod
    def from_json(cls, gym, json_string):
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
