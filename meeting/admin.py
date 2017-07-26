from django.contrib import admin

from . import models

@admin.register(models.PresentRotation)
class RotationAdmin(admin.ModelAdmin):
    list_display = ('order', 'presenter')

admin.site.register(models.MeetingHistory)

@admin.register(models.PresentHistory)
class PresentAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'content')

@admin.register(models.MeetingSkip)
class SkipAdmin(admin.ModelAdmin):
    list_display = ('date', 'reason')
