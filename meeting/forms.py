from django.forms import ModelForm, BooleanField
from django.conf import settings
from . import models

def can_notify():
    return hasattr(settings, 'NOTIFICATION_EMAIL_TO') and hasattr(settings, 'BASE_URL')

class PresentUpdateForm(ModelForm):
    email_notification = BooleanField(required=False, disabled=not can_notify())

    class Meta:
        model = models.PresentHistory
        fields = ['content', 'email_notification']


class TakeLeaveForm(ModelForm):
    email_notification = BooleanField(required=False, disabled=not can_notify())

    class Meta:
        model = models.MeetingAttendance
        fields = ['reason', 'email_notification']
