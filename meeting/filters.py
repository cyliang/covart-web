import django_filters as filters
from . import models

class AttendanceStatusFilter(filters.FilterSet):
    meeting__date = filters.DateRangeFilter()

    class Meta:
        model = models.MeetingAttendance
        fields = ['meeting__date']
