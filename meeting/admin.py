from django.contrib import admin

from .models import PresentRotation, MeetingHistory, PresentHistory

admin.site.register(PresentRotation)
admin.site.register(MeetingHistory)
admin.site.register(PresentHistory)
