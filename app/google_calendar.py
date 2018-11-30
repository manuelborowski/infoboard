# -*- coding: utf-8 -*-

from __future__ import print_function
import datetime
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'

def get_holidays(year=2018):
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('calendar', 'v3', http=creds.authorize(Http()))

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
