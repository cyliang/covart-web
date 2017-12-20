from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django_q.tasks import async
from . import models, slack
from datetime import timedelta, date

def weekly_update():
    models.MeetingHistory.rotate_next_meeting()

def send_notification(body, recipients=None, subject=None, meeting=None, html_body=None):
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

        template_name = 'meeting/postpone_email'
        subject = postponed_date.strftime('Group Meeting Postponed (%m/%d)')
        ret = 'Meeting postponing message sent'
    else:
        # Notify with Slack
        async(slack.send_meeting_notification, next_meeting)

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
