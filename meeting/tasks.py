from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from . import models

def weekly_update():
    models.MeetingHistory.rotate_next_meeting()

def send_meeting_notification(base_url, *recipients):
    next_meeting = models.MeetingHistory.objects.all()[:1][0]

    data = {
        'meeting': next_meeting,
        'presenters': next_meeting.presenters.all(),
        'base_url': base_url,
    }
    text_body = render_to_string('meeting/notify_email.txt', data)
    html_body = render_to_string('meeting/notify_email.html', data)

    mail = EmailMultiAlternatives(
        subject=next_meeting.date.strftime('Group Meeting Notification (%m/%d)'),
        body=text_body,
        to=recipients,
    )
    mail.attach_alternative(html_body, 'text/html')
    mail.send()

