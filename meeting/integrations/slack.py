from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.utils.text import get_text_list
from slackclient.client import SlackClient

def _url(url):
    return settings.BASE_URL + url

class Slack(object):

    def __init__(self, token=None, channel=None):
        token = token or getattr(settings, 'SLACK_TOKEN', None)
        self.channel = channel or getattr(settings, 'SLACK_CHANNEL', None)
        if token == None or self.channel == None:
            raise ImproperlyConfigured("Set SLACK_TOKEN and SLACK_CHANNEL in your setting files.")

        if not hasattr(settings, 'BASE_URL'):
            raise ImproperlyConfigured("Slack apps require BASE_URL in settings being set.")

        self._client = SlackClient(token)

    def __call__(self, method, *args, **kwargs):
        """
        Call SlackClient API with default channel set and error checking.
        """
        kwargs.setdefault('channel', self.channel)
        resp = self._client.api_call(method, *args, **kwargs)
        if not resp['ok']:
            print unicode(resp)
            raise RuntimeError(resp.get('error', unicode(resp)))
        return resp

    def meeting_update(self, meeting):
        attachments = []
        author_ids = []

        # Present Contents
        for present in meeting.presenthistory_set.all():
            attachments += [{
                "fallback": "Presenter %s." % unicode(present.presenter),
                "color": "#439FE0" if present.present_type == present.PAPER_PRESENTATION else "danger",
                "author_name": present.presenter.name,
                "author_link": _url(present.presenter.get_absolute_url()),
                "author_icon": _url(present.presenter.get_picture_url()),
                "title": present.get_present_type_display(),
                "title_link": _url(meeting.get_absolute_url()),
                "text": present.content,
            }]

            try:
                author_ids += [present.presenter.user.social_auth.get(provider='slack').uid]
            except Exception:
                pass

        # Attendees
        attendees = meeting.meetingattendance_set
        ontime = attendees.filter(status=attendees.model.PRESENT_ON_TIME)
        late = attendees.filter(status=attendees.model.LATE)
        absent = filter(lambda a: not a.get_is_present(), attendees.all())
        attend_fields = [{
            "title": "On Time",
            "value": get_text_list(
                list(ontime.values_list('member__name', flat=True)),
                "and"
            ),
        }]
        if late.exists():
            attend_fields += [{
                "title": "Late",
                "value": get_text_list(
                    list(late.values_list('member__name', flat=True)),
                    "and"
                ),
                "short": True,
            }]
        if len(absent) > 0:
            attend_fields += [{
                "title": "Leave / Absent",
                "value": get_text_list(
                    [a.member.name for a in absent],
                    "and"
                ),
                "short": True,
            }]
        attachments += [{
            "fallback": "",
            "fields": attend_fields,
        }]

        # Button Actions
        attachments += [{
            "fallback": "Go %s for detail." % _url(meeting.get_absolute_url()),
            "actions": [
                {
                    "type": "button",
                    "text": "Detail",
                    "url": _url(meeting.get_absolute_url()),
                    },
                {
                    "type": "button",
                    "text": "Take Leave",
                    "url": _url(reverse('meeting:take-leave', kwargs={'meeting': meeting.date})),
                    "style": "danger",
                },
            ],
        }]

        text = meeting.date.strftime('Group Meeting Notification: *%A, %b %d, %Y*')
        text += '\n' + ' '.join(['<@%s>' % id for id in author_ids])

        # Send Slack request
        req = {
            "text": text,
            "attachments": attachments,
            "icon_url": _url(static('slack/presentation.png')),
            "username": 'Meeting Bot',
        }

        if meeting.slack_ts == '':
            resp = self("chat.postMessage", **req)

            meeting.slack_ts = resp['ts']
            meeting.save_without_sync()
        else:
            resp = self("chat.update", ts=meeting.slack_ts, **req)

        return unicode(resp)

    def send_postponed(self, meeting, postponed_date, reason):
        text = "There will be *no* group meeting next week (%A, %b %d, %Y)"
        text = postponed_date.strftime(text) + ("%s.\n" % reason.lower())
        text += "The next group meeting has been postponed to "
        text += meeting.date.strftime("%A, %b %d, %Y. ")
        text += "Presenters will be %s." % get_text_list(
            map(unicode, meeting.presenters.all()), 'and'
        )

        attachments = [{
            "fallback": "Go %s for detail." % _url(meeting.get_absolute_url()),
            "actions": [{
                "type": "button",
                "text": "Detail",
                "url": _url(meeting.get_absolute_url()),
            }]
        }]

        return unicode(self("chat.postMessage",
            text=text,
            attachments=attachments,
            icon_url=_url(static('slack/presentation.png')),
            username='Meeting Bot',
        ))

    def delete_message(self, ts):
        return self("chat.delete", ts=ts)

