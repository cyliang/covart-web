from django.contrib import admin

from .models import PresentRotation, MeetingHistory, PresentHistory

@admin.register(PresentRotation)
class RotationAdmin(admin.ModelAdmin):
    list_display = ('order', 'presenter')

admin.site.register(MeetingHistory)

@admin.register(PresentHistory)
class PresentAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'content')
