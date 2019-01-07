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
- `credentials.json`: Google Calendar API credentials, which need to be generated from Google's website.
- `token.json`: Created by the OAuth code for calendar authentication.  See the Google API reference for more details.
- `secrets.py`: Contains calendar IDs used for the endpoints for the created events.

## Notes
- The Gold's Gym website is notoriously slow, and requests for API data have taken up to 10 seconds to complete.
- Sometimes requests fail, and as a bit of a brute force attempt to deal with this, the script will try each request a maximum of 3 times.
- Deleting events off of the calendar is an issue, and the script will not be able to recreate them.  There appears to be
some sort of issue with the "Trash" for the calendars.  After deleting events, and clearing the trash, the unique IDs
assigned to each event by the script are thrown back in an error message claiming they still exist.

## Future Features
- [ ] Configure runs via a file listing the classes you wanted, and what calendars they map to
- [ ] Create database of gyms with IDs, addresses, etc from the API.  Add to the gym object for automatic data population