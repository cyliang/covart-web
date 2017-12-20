from django.conf import settings
from django.urls import reverse
from django.contrib.staticfiles.templatetags.staticfiles import static
from slackclient.client import SlackClient

def __url(url):
    return settings.BASE_URL + url

def get_slack():
    return SlackClient(settings.SLACK_TOKEN)

def send_meeting_notification(meeting):
    slack = get_slack()
    attachments = []
    author_ids = []

    # Present Contents
    for present in meeting.presenthistory_set.all():
        attachments += [{
            "fallback": "Presenter %s." % unicode(present.presenter),
            "color": "#439FE0" if present.present_type == present.PAPER_PRESENTATION else "danger",
            "author_name": present.presenter.name,
            "author_link": __url(present.presenter.get_absolute_url()),
            "author_icon": __url(present.presenter.get_picture_url()),
            "title": present.get_present_type_display(),
            "title_link": __url(meeting.get_absolute_url()),
            "text": present.content,
        }]

        try:
            author_ids += [present.presenter.user.social_auth.get(provider='slack').uid]
        except Exception:
            pass

    # Button Actions
    attachments += [{
        "fallback": "Go %s for detail." % __url(meeting.get_absolute_url()),
        "actions": [
            {
                "type": "button",
                "text": "Detail",
                "url": __url(meeting.get_absolute_url()),
                },
            {
                "type": "button",
                "text": "Take Leave",
                "url": __url(reverse('meeting:take-leave', kwargs={'meeting': meeting.date})),
                "style": "danger",
            },
        ],
    }]

    text = meeting.date.strftime('Group Meeting Notification: *%A, %b %d, %Y*')
    text += '\n' + ' '.join(['<@%s>' % id for id in author_ids])

    # Send Slack request
    req = {
        "channel": settings.SLACK_CHANNEL,
        "text": text,
        "attachments": attachments,
        "icon_url": __url(static('slack/presentation.png')),
        "username": 'Meeting Bot',
    }

    del meeting.slack_ts
    if meeting.slack_ts == '':
        resp = slack.api_call("chat.postMessage", **req)

        meeting.slack_ts = resp['ts']
        meeting.save()
    else:
        resp = slack.api_call("chat.update", ts=meeting.slack_ts, **req)

    return ("Successfully" if resp['ok'] else "Failed to") + " post/update to Slack"

