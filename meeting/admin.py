from django.contrib import admin

from . import models

@admin.register(models.PresentRotation)
class RotationAdmin(admin.ModelAdmin):
    list_display = ('order', 'presenter')


class AttendanceInlineAdmin(admin.TabularInline):
    model = models.MeetingAttendance
    extra = 0

class PresentInlineAdmin(admin.TabularInline):
    model = models.PresentHistory
    extra = 0

@admin.register(models.MeetingHistory)
class MeetingAdmin(admin.ModelAdmin):
    search_fields = ('presenthistory__content', 'presenters__name')
    list_filter = ('date', 'presenters')
    list_display = ('__unicode__', 'get_presenters', 'get_contents')
    inlines = (PresentInlineAdmin, AttendanceInlineAdmin)

    def get_presenters(self, record):
        return ', '.join(map(unicode, record.presenters.all()))
    get_presenters.short_description = 'Presenters'

    def get_contents(self, record):
        return ', '.join(
            [
                '"%s..."' % ph.content[:20]
                for ph in record.presenthistory_set.all()
                if ph.content != ""
            ]
        )
    get_contents.short_description = 'Content'


@admin.register(models.MeetingSkip)
class SkipAdmin(admin.ModelAdmin):
    list_display = ('date', 'reason')

admin.site.register(models.ExpectedAttendance)
