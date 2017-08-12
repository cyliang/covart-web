from django.forms import ModelForm, BooleanField
from . import models

class PresentUpdateForm(ModelForm):
    email_notification = BooleanField(required=False, disabled=True)

    class Meta:
        model = models.PresentHistory
        fields = ['content', 'email_notification']
