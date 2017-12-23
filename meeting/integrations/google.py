from django.conf import settings
from django.db.models import Q
from django.core.exceptions import ImproperlyConfigured
from django.utils.timezone import make_aware, get_default_timezone_name
from django.utils.text import get_text_list
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
import httplib2

class GoogleClient(object):
    SERVICE_SECRET_FILE = 'covart/service_secret.json'

    # Override the following attributes in derived classes.
    service = ''
    version = ''
    scope = []

    def __init__(self):
        cred = ServiceAccountCredentials.from_json_keyfile_name(
            self.SERVICE_SECRET_FILE,
            self.scope)
        http = cred.authorize(httplib2.Http())

        self._client = build(self.service, self.version, http=http)

    def __call__(self):
        return self._client


class GoogleCalendar(GoogleClient):
    service = 'calendar'
    version = 'v3'
    scope = ['https://www.googleapis.com/auth/calendar']

    def __init__(self, calendar_id=None, *args, **kwargs):
        self.calendar_id = calendar_id or getattr(settings, 'GOOGLE_CALENDAR_ID', None)
        if self.calendar_id == None:
            raise ImproperlyConfigured("Set GOOGLE_CALENDAR_ID in settings to sync with Google Calendar")
        super(GoogleCalendar, self).__init__(*args, **kwargs)

    def delete_event(self, event_id):
        try:
            self().events().delete(
                calendarId=settings.GOOGLE_CALENDAR_ID,
                eventId=event_id,
            ).execute()
        except HttpError as e:
            # The calendar event may be accidentally deleted.
            if e.resp != 404:
                raise e
        return 'Event deleted successfully.'

    def sync_meeting(self, meeting):
        # Get meeting time with timezone
        start = make_aware(datetime.combine(meeting.date, settings.MEETING_START_TIME))
        end = start + settings.MEETING_DURATION
        timezone = get_default_timezone_name()

        # Add present content as event description
        description = 'Presenters are %s.\n\n' % get_text_list(
            map(unicode, meeting.presenters.all()), 'and'
        ) + '\n\n'.join([
            '%s: %s' % (unicode(p.presenter), p.content)
            for p in meeting.presenthistory_set.all()
        ])

        attendees = [
            {
                'email': a.member.get_internal_email(),
                'displayName': a.member.name,
                'responseStatus': 'accepted' if a.get_is_present() else 'declined',
            }
            for a in meeting.meetingattendance_set.all()
            if a.member.get_internal_email() != None
        ]

        body = {
            'summary': 'Group Meeting',
            'location': settings.MEETING_LOCATION,
            'description': description,
            'start': {
                'dateTime': start.isoformat(),
                'timeZone': timezone,
            },
            'end': {
                'dateTime': end.isoformat(),
                'timeZone': timezone,
            },
            'source': {
                'title': unicode(meeting),
                'url': settings.BASE_URL + meeting.get_absolute_url()
            },
            'attendees': attendees,
        }

        if meeting.gcal_id != "":
            try:
                event = self().events().update(
                    calendarId=settings.GOOGLE_CALENDAR_ID,
                    eventId=meeting.gcal_id,
                    body=body,
                ).execute()

                return "Meeting event updated."
            except HttpError as e:
                # The calendar event may be accidentally deleted.
                if e.resp != 404:
                    raise e

        event = self().events().insert(
            calendarId=settings.GOOGLE_CALENDAR_ID,
            body=body,
        ).execute()

        meeting.gcal_id = event['id']
        meeting.save_without_sync()
        return unicode(event)

