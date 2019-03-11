# Gold's Gym Google Calendar Integration
This script is an attempt to make the class schedules for the Spin classes I attend at the gym more accessible. 
It pulls the class information from Gold's website's API for all three local gym branches, filters out
non-Spin classes, and adds classes from each location to a specific existing Google calendar.

Events are given a unique ID based on the numeric gym ID, instructor ID, class ID, and the start & end times of the class.
This information is then hashed, and used as the calendar event ID.  This enables the script to check if events already exist,
and if so, update them with the most recent data.  If an event doesn't exist, it is created.

*Disclaimer:* as this was a lazy Sunday afternoon project, I make no claims that the program is robust or 
written well...but it does work!

## Files
- `main.py`: main script.  Run this in the terminal to load up the calendars.
- `config.py`: general configuration options for the script - look here first!
- `gym.py`: class describing a single Gym.  Contains API query methods and a list of classes at the gym.
- `gym_class.py`: class describing a single Gym Class.
- `service.json`: Google Service Account credentials.  Information on how to generate this file is 
[here](https://developers.google.com/identity/protocols/OAuth2ServiceAccount)
- `secrets.py`: contains calendar IDs used for the endpoints for the created events.  Also contains mapping for 
which calendar to use for which gym's events.

## Use
1. Install necessary packages from `requirements.txt` using pip
2. Set up the Google Calendar API and obtain service account credentials.  Follow the link above under 
`credentials.json` to generate.  Service account credentials should be included in the root directory and named 
`service.json`
3. Obtain your gym ID's from the Gold's website.  It is a 4 digit number and has to be pulled from the API call using
Chrome Developer Tools in the Network tab.
4. Configure the list of gyms in `config.py`.  Edit any other options here as well (class filter, etc)
5. Get calendar ID for the target calendars (one gym -> one calendar) and enter into `secrets.json`.  Add any invitee
email addresses here as well for the created events.
6. Run `main.py` in a terminal!

## Docker
I run this script automatically on a cloud server, so my Dockerfile is included to make things easy if you want to 
do the same.  It expects a configured `service.json` file and your completed `secrets.py` file as well.  You must edit 
those before running a build for the script to work.

## Notes
- A Google Service account is required for use of this script.  
- The Gold's Gym website is notoriously slow, and requests for API data have taken up to 10 seconds to complete.
- Sometimes requests fail, and as a bit of a brute force attempt to deal with this, the script will try each 
request a maximum of 3 times.
- Deleting events off of the calendar is an issue, and the script will not be able to recreate them.  There appears 
to be some sort of issue with the "Trash" for the calendars.  After deleting events, and clearing the trash, the unique 
IDs assigned to each event by the script are thrown back in an error message claiming they still exist.

## Future Features
- [ ] Configure runs via a file listing the classes you wanted, and what calendars they map to
    - Partially done - class filter is now available in config.py
- [ ] Create database of gyms with IDs, addresses, etc from the API.  Add to the gym object for automatic data population
    - [x] Add gym selections to config.py
- [ ] Create validation function for config.py and secrets.py
- [x] Add ability to adjust time of event by either extending the start time earlier, or end time later (to account for travel, etc) 
