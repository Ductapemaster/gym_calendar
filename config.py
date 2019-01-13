# This file contains general configuration for how the program should load classes and create calendar events
# No secret information is included in this file

# This list should include the class names you wish to filter the classes received from the API by.
# Only classes matching the names in this list will have calendar events created for them.
class_filter = ["GGX Cycle"]

# This is the timezone that calendar events should be created with
# A list of valid timezone strings can be found here: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
event_timezone = "America/Los_Angeles"

# The number of weeks to pull calendar events from
# For example if weeks_to_grab = 1, the script will pull events from the current week only.
# If weeks_to_grab = 2, the script will pull events from the current week, and next week.
weeks_to_grab = 2

# List of the gyms to scan for available classes from
# You must obtain the gym's id_number by browsing classes from that gym and extracting the number from the URL
gyms = [
    {
        'id_number': 1849,
        'address': "Gold's Gym Goleta 6144 Calle Real Suite 101 Goleta CA 93117",
        'shortname': "Goleta",
    },
    {
        'id_number': 1848,
        'address': "Gold's Gym Uptown 3908 State Street Santa Barbara CA 93105",
        'shortname': "Uptown",
    },
    {
        'id_number': 1847,
        'address': "Gold's Gym Downtown 21 W. Carrillo Street Santa Barbara CA 93101",
        'shortname': "Downtown",
    }
]