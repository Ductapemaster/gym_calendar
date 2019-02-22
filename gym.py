import logging
import requests
from datetime import timedelta, datetime
from gym_class import GymClass

logger_gym = logging.getLogger("gym")


class Gym:
    def __init__(self, id_number, address, shortname, target_calendar="primary"):
        self.id_number = id_number
        self.address = address
        self.shortname = shortname
        self.target_calendar = target_calendar
        self.classes = []

        logger_gym.debug("Create instance of Gym object: {}".format(self.__repr__()))

    def __repr__(self):
        return "{} ({}): {}".format(self.shortname, self.id_number, self.address)

    def generate_request_url(self, day_offset=0):

        api_url_prefix = "https://www.goldsgym.com/api"
        target_date = datetime.now() + timedelta(days=day_offset)
        url = "/".join([api_url_prefix,
                        "gyms",
                        str(self.id_number),
                        "schedules",
                        "currentWeek?targetDate={}".format(target_date.strftime("%Y-%m-%d"))
                        ])

        logger_gym.debug('Generated Gym API URL: {}'.format(url))
        return url

    def query_classes(self, day_offset=0, retries=3):

        # Perform API requests
        data = None
        url = self.generate_request_url(day_offset=day_offset)
        while data is None and retries > 0:
            try:
                data = requests.get(url=url).json()
                logger_gym.info("Request to {} completed".format(url))
            except Exception as e:
                logger_gym.warning("Request to {} FAILED".format(url))
                data = None
            finally:
                retries -= 1

        # Process received class list into our data structure
        if data is not None:
            for day in data.keys():
                for gym_class_data in data[day]:
                    self.classes.append(GymClass(self, json_string=gym_class_data))
        else:
            logger_gym.error("Retries for url {} exceeded - forfeiting".format(url))

        logger_gym.debug("{} classes retrieved from url {}".format(len(self.classes), url))

    def filtered_classes(self, filter):
        return [gym_class for gym_class in self.classes if gym_class.class_name in filter]
