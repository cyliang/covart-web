import django_filters as filters
from . import models
from website import models as website_models

class AttendanceStatusFilter(filters.FilterSet):
    meeting__date = filters.DateRangeFilter()

    class Meta:
        model = models.MeetingAttendance
        fields = ['meeting__date']


class AttendanceStatMeetingFilter(filters.FilterSet):
    date = filters.DateRangeFilter()

    class Meta:
        model = models.MeetingHistory
        fields = ['date']

class AttendanceStatMemberFilter(filters.FilterSet):
    date = filters.DateRangeFilter(name='attending__date')

    class Meta:
        model = website_models.Member
        fields = ['date']
