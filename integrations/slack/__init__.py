from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from slackclient.client import SlackClient

class Slack(object):

    def __init__(self, channel=None, token=None):
        token = token or getattr(settings, 'SLACK_TOKEN', None)
        if channel:
            self.channel = channel

        if token == None:
            raise ImproperlyConfigured("Set SLACK_TOKEN in your setting.")

        self._client = SlackClient(token)

    def __call__(self, method, *args, **kwargs):
        """
        Call SlackClient API with default channel set and error checking.
        """
        if hasattr(self, 'channel'):
            kwargs.setdefault('channel', self.channel)
        resp = self._client.api_call(method, *args, **kwargs)
        if not resp['ok']:
            print unicode(resp)
            raise RuntimeError(resp.get('error', unicode(resp)))
        return resp

    def delete_message(self, ts):
        return self("chat.delete", ts=ts)

