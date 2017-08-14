from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from . import models
from datetime import timedelta, date

def weekly_update():
    models.MeetingHistory.rotate_next_meeting()

def send_rollcall_notification(base_url):
    """
    This task send a rollcall notification to each presenter.
    """

    try:
        meeting = models.MeetingHistory.objects.get(date=date.today())
    except models.MeetingHistory.DoesNotExist:
        return 'There is no meeting today. Aborted.'

    data = {
        'meeting': meeting,
        'base_url': base_url,
    }

    text_body = render_to_string('meeting/rollcall_email.txt', data)
    html_body = render_to_string('meeting/rollcall_email.html', data)

    def get_email(member):
        if not member.user:
            return None

        email = member.user.email
        social = member.user.social_auth.filter(provider='google-auth2')
        if not email and social.exists():
            email = social[0].uid

        return email

    mail = EmailMultiAlternatives(
        subject=meeting.date.strftime('Rollcall Notification (%m/%d)'),
        body=text_body,
        to=filter(lambda e: e != None, map(get_email, meeting.presenters.all())),
    )
    mail.attach_alternative(html_body, 'text/html')
    mail.send()

def send_meeting_notification(base_url, *recipients):
    next_meeting = models.MeetingHistory.objects.all()[:1][0]

    data = {
        'meeting': next_meeting,
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

