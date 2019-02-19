# Gold's Gym Google Calendar Integration
This script is an attempt to make the class schedules for the Spin classes I attend at the gym more accessible. 
It pulls the class information from Gold's website's API for all three local gym branches, filters out
non-Spin classes, and adds classes from each location to a specific existing Google calendar.

Events are given a unique ID based on the numeric gym ID, instructor ID, class ID, and the start & end times of the class.
This information is then hashed, and used as the calendar event ID.  This enables the script to check if events already exist,
and if so, update them with the most recent data.  If an event doesn't exist, it is created.

*Disclaimer:* as this was a lazy Sunday afternoon project, I make no claims that the program is robust or written well...but it does work!

## Files
- `main.py`: main script.  Run this in the terminal to load up the calendars.
- `credentials.json`: Google Service Account credentials.  Information on how to generate this file is [here](https://developers.google.com/identity/protocols/OAuth2ServiceAccount)
- `secrets.py`: Contains calendar IDs used for the endpoints for the created events.

## Notes
- A Google Service account is required for use of this script.  Follow the link above under `credentials.json` to generate.
- The Gold's Gym website is notoriously slow, and requests for API data have taken up to 10 seconds to complete.
- Sometimes requests fail, and as a bit of a brute force attempt to deal with this, the script will try each request a maximum of 3 times.
- Deleting events off of the calendar is an issue, and the script will not be able to recreate them.  There appears to be
some sort of issue with the "Trash" for the calendars.  After deleting events, and clearing the trash, the unique IDs
assigned to each event by the script are thrown back in an error message claiming they still exist.

## Future Features
- [ ] Configure runs via a file listing the classes you wanted, and what calendars they map to
    - Partially done - class filter is now available in config.py
- [ ] Create database of gyms with IDs, addresses, etc from the API.  Add to the gym object for automatic data population
    - [x] Add gym selections to config.py
- [ ] Create validation function for config.py and secrets.py
- [ ] Add ability to adjust time of event by either extending the start time earlier, or end time later (to account for travel, etc) 
