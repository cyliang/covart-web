from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
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
