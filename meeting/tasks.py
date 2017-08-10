from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from . import models
from datetime import timedelta, date

def weekly_update():
    models.MeetingHistory.rotate_next_meeting()

def send_meeting_notification(base_url, *recipients):
    next_meeting = models.MeetingHistory.objects.all()[:1][0]

    data = {
        'meeting': next_meeting,
        'presenters': next_meeting.presenters.all(),
        'base_url': base_url,
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
        template_name = 'meeting/notify_email'
        subject = next_meeting.date.strftime('Group Meeting Notification (%m/%d)')
        ret = 'Meeting notification for %s sent.' % unicode(next_meeting)

    text_body = render_to_string(template_name + '.txt', data)
    html_body = render_to_string(template_name + '.html', data)

    mail = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        to=recipients,
    )
    mail.attach_alternative(html_body, 'text/html')
    mail.send()
    return ret

