import httplib2
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

SERVICE_SECRET_FILE = 'covart/service_secret.json'

SCOPES = {
    'calendar': ['https://www.googleapis.com/auth/calendar'],
}

def get(service, version):
    try:
        cred = ServiceAccountCredentials.from_json_keyfile_name(
            SERVICE_SECRET_FILE,
            SCOPES[service])
    except KeyError:
        raise ValueError('Invalid service argument.')

    http = cred.authorize(httplib2.Http())
    return build(service, version, http=http)
