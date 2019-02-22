# -*- coding: utf-8 -*-

from __future__ import print_function
import datetime
from googleapiclient.discovery import build
from . import app

def get_holidays(year=2018):
    service = build('calendar', 'v3', developerKey=app.config['GOOGLE_CALENDAR_API_KEY'], cache_discovery=False)

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    timeMin = datetime.datetime(year,1,1).isoformat() + 'Z' # 'Z' indicates UTC time
    timeMax = datetime.datetime(year,12,31).isoformat() + 'Z' # 'Z' indicates UTC time

    events_result = service.events().list(calendarId='feestdagenbelgie@gmail.com', timeMin=timeMin,
                                        timeMax=timeMax, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    return events

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
#        end = event['end'].get('dateTime', event['end'].get('date'))
#        start = event['start']['date']
        end = event['end']['date']

        print(start, end, event['summary'])
        print(type(start))

if __name__ == '__main__':
    hl = get_holidays()
    for event in hl:
        start = event['start']['date']
        end = event['end']['date']

        print(start, end, event['summary'])
