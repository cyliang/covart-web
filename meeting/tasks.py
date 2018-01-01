from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.text import get_text_list
from django_q.tasks import async
from datetime import timedelta, date, datetime
from . import models

def _url(url):
    if not hasattr(settings, "BASE_URL"):
        raise ImproperlyConfigured("Set BASE_URL in your settings.")
    return "%s%s" % (settings.BASE_URL, url)

def _get_slack():
    from integrations.slack import Slack
    try:
        return Slack(settings.SLACK_MEETING_CHANNEL)
    except AttributeError:
        raise ImproperlyConfigured("Set SLACK_MEETING_CHANNEL in settings.")

def _get_gcal():
    from integrations.google import GoogleCalendar
    return GoogleCalendar()

def run_slack(*args, **kwargs):
    from integrations.slack import Slack
    slack = Slack()
    return slack(*args, **kwargs)

def sync_meeting_with_slack(meeting):
    try:
        meeting = models.MeetingHistory.objects.get(pk=meeting.pk)
    except models.MeetingHistory.DoesNotExist:
        return "Meeting %s is already deleted" % unicode(meeting)

    from django.urls import reverse
    from django.contrib.staticfiles.templatetags.staticfiles import static

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
        "callback_id": "meeting_%s_take-leave" % unicode(meeting.date),
        "actions": [
            {
                "type": "button",
                "text": "Detail",
                "url": _url(meeting.get_absolute_url()),
                },
            {
                "type": "button",
                "text": "Take Leave",
                "name": "take-leave",
                "value": "open-modal",
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

    slack = _get_slack()
    if meeting.slack_ts == '':
        resp = slack("chat.postMessage", **req)

        meeting.slack_ts = resp['ts']
        meeting.save_without_sync()
    else:
        resp = slack("chat.update", ts=meeting.slack_ts, **req)

    return unicode(resp)

def send_slack_postponed_meeting(meeting, postponed_date, reason):
    from django.contrib.staticfiles.templatetags.staticfiles import static

    text = "There will be *no* group meeting next week (%A, %b %d, %Y)"
    text = postponed_date.strftime(text) + ("%s.\n" % reason.lower())
    text += "The next group meeting has been postponed to "
    text += meeting.date.strftime("%A, %b %d, %Y. ")
    text += "Presenters will be %s." % get_text_list(
        map(unicode, meeting.presenters.all()), 'and'
    )

    attachments = [{
        "fallback": "Go %s for detail." % _url(
            meeting.get_absolute_url()),
        "actions": [{
            "type": "button",
            "text": "Detail",
            "url": _url(meeting.get_absolute_url()),
        }]
    }]

    slack = _get_slack()
    return unicode(slack("chat.postMessage",
        text=text,
        attachments=attachments,
        icon_url=_url(static('slack/presentation.png')),
        username='Meeting Bot',
    ))

def sync_meeting_with_gcal(meeting):
    try:
        meeting = models.MeetingHistory.objects.get(pk=meeting.pk)
    except models.MeetingHistory.DoesNotExist:
        return "Meeting %s is already deleted" % unicode(meeting)

    from django.utils.timezone import make_aware, get_default_timezone_name
    from googleapiclient.errors import HttpError

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

    gcal = _get_gcal()
    if meeting.gcal_id != "":
        try:
            event = gcal().events().update(
                calendarId=settings.GOOGLE_CALENDAR_ID,
                eventId=meeting.gcal_id,
                body=body,
            ).execute()

            return "Meeting event updated."
        except HttpError as e:
            # The calendar event may be accidentally deleted.
            if e.resp != 404:
                raise e

    event = gcal().events().insert(
        calendarId=settings.GOOGLE_CALENDAR_ID,
        body=body,
    ).execute()

    meeting.gcal_id = event['id']
    meeting.save_without_sync()
    return unicode(event)

def delete_slack_msg(ts):
    return _get_slack().delete_message(ts)

def delete_gcal_event(event_id):
    from googleapiclient.errors import HttpError

    gcal = _get_gcal()
    try:
        gcal().events().delete(
            calendarId=settings.GOOGLE_CALENDAR_ID,
            eventId=event_id,
        ).execute()
    except HttpError as e:
        # The calendar event may be accidentally deleted.
        if e.resp != 404:
            raise e
    return 'Event deleted successfully.'

def weekly_update():
    models.MeetingHistory.rotate_next_meeting()

def send_notification(body, recipients=None, subject=None, meeting=None, html_body=None):
    from django.core.mail import EmailMultiAlternatives

    if not subject and not meeting:
        raise ValueError('There must be the argument "meeting" if the argument "subject" is missing.')

    mail = EmailMultiAlternatives(
        subject=subject or meeting.get_email_title(),
        body=body,
        to=recipients or [settings.NOTIFICATION_EMAIL_TO],
    )
    if html_body:
        mail.attach_alternative(html_body, 'text/html')

    mail.send()

def rollcall_notification():
    """
    This task send a rollcall notification to each presenter.
    """
    from django.template.loader import render_to_string

    try:
        meeting = models.MeetingHistory.objects.get(date=date.today())
    except models.MeetingHistory.DoesNotExist:
        return 'There is no meeting today. Aborted.'

    data = {
        'meeting': meeting,
        'base_url': settings.BASE_URL,
    }

    text_body = render_to_string('meeting/rollcall_email.txt', data)
    html_body = render_to_string('meeting/rollcall_email.html', data)

    def get_email(member):
        return member.get_internal_email()

    send_notification(
        subject=meeting.date.strftime('Rollcall Notification (%m/%d)'),
        recipients=filter(lambda e: e != None, map(get_email, meeting.presenters.all())),
        body=text_body,
        html_body=html_body,
    )

def meeting_notification():
    from django.template.loader import render_to_string

    next_meeting = models.MeetingHistory.objects.all()[:1][0]

    data = {
        'meeting': next_meeting,
        'base_url': settings.BASE_URL,
    }

    if next_meeting.date - date.today() > timedelta(days=7):
        # The meeting is postponed.
        postponed_date = models.MeetingHistory.get_next_meeting_date()

        reason = ''
        skip = list(models.MeetingSkip.objects.filter(date=postponed_date))
        if len(skip) > 0 and skip[0].reason != '':
            reason = ' because of %s' % skip[0].reason

        data['postponed_date'] = postponed_date
        data['reason'] = reason

        # Notify with Slack
        async(send_slack_postponed_meeting, next_meeting, postponed_date, reason)

        template_name = 'meeting/postpone_email'
        subject = postponed_date.strftime('Group Meeting Postponed (%m/%d)')
        ret = 'Meeting postponing message sent'
    else:
        # Notify with Slack
        async(sync_meeting_with_slack, next_meeting)

        template_name = 'meeting/notify_email'
        subject = next_meeting.get_email_title()
        ret = 'Meeting notification for %s sent.' % unicode(next_meeting)

    text_body = render_to_string(template_name + '.txt', data)
    html_body = render_to_string(template_name + '.html', data)

    send_notification(
        subject=subject,
        body=text_body,
        html_body=html_body,
    )

    return ret
