from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from slackclient.client import SlackClient

class Slack(object):

    def __init__(self, channel=None, token=None):
        """
        Instantiate a Slack API caller wrapper.
        Specify `channel` to set default channel for future API calls.
        If token is not specified, the one in your settings will be used.
        """
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
        """
        A quick helper to delete a message.
        """
        return self("chat.delete", ts=ts)

def call_slack(*args, **kwargs):
    """
    A quick utility to make one Slack API call.
    If token is not specified in kwargs, the one in your settings will be used.
    """
    slack = Slack(token=kwargs.pop('token', None))
    return slack(*args, **kwargs)

def async_call_slack(*args, **kwargs):
    """
    Try to call Slack API in asynchronous way if there is a cluster configured
    with Django Q; otherwise, fallback to synchronous call.
    If token is not specified in kwargs, the one in your settings will be used.

    You can also specify `hook` to do post-call actions.
    """
    try:
        from django_q.tasks import async
    except ImportError:
        # Fallback to synchronous call
        call_slack(*args, **kwargs)
    else:
        kwargs.setdefault('hook', ('%s.%s' % (
            _async_hook.__module__, _async_hook.__name__)))
        async(call_slack, *args, **kwargs)

def _async_hook(task):
    """
    Make every finished task success to prevent retrying because retrying is
    often useless anyway.
    """
    task.success = True
