from __future__ import unicode_literals

from django.db import models
from django.conf import settings
from django.urls import reverse
from datetime import date, timedelta, datetime
from django_q.tasks import async

class PresentRotation(models.Model):
    """
    A ring buffer storing a fixed order of presenters for each meeting type.
    Adjust the attribute `order` to reorder the rotation. The rotation with
    smaller `order` goes first.
    """

    order     = models.IntegerField(unique=True)
    presenter = models.OneToOneField('website.Member', models.CASCADE)
    join_date = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __unicode__(self):
        return "%d: %s" % (self.order, self.presenter)

    @classmethod
    def add_person_after(cls, member, after_rotation):
        """
        Insert a member originally not in the rotation with a desired order.
        return: The newly created `PresentRotation`.
        member: The `Member` to insert into the rotation.
        after_rotation: The `PresentRotation` to insert after.
        """

        order = after_rotation.order

        if cls.objects.get(order=order+1):
            for rotation in cls.objects.filter(order__gt=order).order_by('-order'):
                rotation.order += 1
                rotation.save()

        return cls.objects.create(order=order+1, presenter=member)

    def get_after(self):
        """
        Get next rotation of current rotation.
        """

        manager = self.__class__.objects
        after   = manager.filter(order__gt=self.order).order_by('order')[:1]

        if after:
            return after[0]
        else:
            return manager.all().order_by('order')[0]


def sync_meeting_with_gcal(meeting):
    from . import google
    from django.utils.timezone import make_aware, get_default_timezone_name
    from django.utils.text import get_text_list
    from django.db.models import Q
    from googleapiclient.errors import HttpError

    if not hasattr(settings, 'GOOGLE_CALENDAR_ID'):
        print "Set GOOGLE_CALENDAR_ID in settings to sync with Google Calendar"
        return "Sync aborted due to improper settings"

    # Get meeting time with timezone
    start = make_aware(datetime.combine(meeting.date, settings.MEETING_START_TIME))
    end = start + settings.MEETING_DURATION
    timezone = get_default_timezone_name()

    # Add present content as event description
    description = 'Presenters are %s.\n\n' % get_text_list(
        map(unicode, meeting.presenters.all()), 'and'
    ) + '\n\n'.join([
        '%s: %s' % (p.presenter, p.content)
        for p in meeting.presenthistory_set.all()
    ])

    attendees = [
        {
            'email': a.member.get_internal_email(),
            'displayName': a.member.name,
            'responseStatus': 'accepted' if a.get_is_present() else 'declined',
        }
        for a in meeting.meetingattendance_set.all()
        if a.member.get_internal_email() != None
    ]

    body = {
        'summary': 'Group Meeting',
        'location': settings.MEETING_LOCATION,
        'description': description,
        'start': {
            'dateTime': start.isoformat(),
            'timeZone': timezone,
        },
        'end': {
            'dateTime': end.isoformat(),
            'timeZone': timezone,
        },
        'source': {
            'title': unicode(meeting),
            'url': settings.BASE_URL + meeting.get_absolute_url()
        },
        'attendees': attendees,
    }

    calendar = google.get('calendar', 'v3')

    if meeting.gcal_id != "":
        try:
            event = calendar.events().update(
                calendarId=settings.GOOGLE_CALENDAR_ID,
                eventId=meeting.gcal_id,
                body=body,
            ).execute()

            return "Meeting event updated."
        except HttpError as e:
            # The calendar event may be accidentally deleted.
            if e.resp != 404:
                raise e

    event = calendar.events().insert(
        calendarId=settings.GOOGLE_CALENDAR_ID,
        body=body,
    ).execute()

    meeting.gcal_id = event['id']
    meeting.save_without_sync()
    return "Meeting event created: %s" % event.get('htmlLink', '')

def delete_gcal_event(event_id):
    from . import google
    from googleapiclient.errors import HttpError

    try:
        google.get('calendar', 'v3').events().delete(
            calendarId=settings.GOOGLE_CALENDAR_ID,
            eventId=event_id,
        ).execute()
    except HttpError as e:
        # The calendar event may be accidentally deleted.
        if e.resp != 404:
            raise e

    return 'Event deleted successfully.'

class MeetingHistory(models.Model):
    """
    The history for past meetings and one coming meeting.
    """

    date          = models.DateField(unique=True)
    last_rotation = models.ForeignKey('PresentRotation', models.SET_NULL, null=True)
    presenters    = models.ManyToManyField(
        'website.Member',
        through='PresentHistory',
        through_fields=('meeting', 'presenter'),
        related_name='presenting',
    )
    attendance    = models.ManyToManyField(
        'website.Member',
        through='MeetingAttendance',
        through_fields=('meeting', 'member'),
        related_name='attending',
    )
    gcal_id       = models.CharField(max_length=150, blank=True)

    class Meta:
        ordering = ['-date']

    def __unicode__(self):
        return "%s Group Meeting" % unicode(self.date)

    def get_absolute_url(self):
        return reverse('meeting:detail', args=[self.date])

    def save(self, *args, **kwargs):
        """
        Sync the meeting with Google Calendar after saving.
        """

        ret = super(MeetingHistory, self).save(*args, **kwargs)
        async(sync_meeting_with_gcal, self)
        return ret

    def save_without_sync(self, *args, **kwargs):
        return super(MeetingHistory, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.gcal_id != '':
            async(delete_gcal_event, self.gcal_id)
        return super(MeetingHistory, self).delete(*args, **kwargs)

    def not_yet_happened(self):
        return self.date > date.today()

    def get_attendance_statistics(self):
        attendance = self.meetingattendance_set
        expected = attendance.all().count()
        on_time = attendance.filter(status=MeetingAttendance.PRESENT_ON_TIME).count()
        late = attendance.filter(status=MeetingAttendance.LATE).count()

        return {
            'expected': expected,
            'PRESENT_ON_TIME': on_time,
            'LATE': late,
            'not_present': expected - on_time - late,
            'present_rate': (on_time + late) * 100 / expected if expected != 0 else 100,
        }

    def get_email_title(self):
        return self.date.strftime('Group Meeting Notification (%m/%d)')

    @classmethod
    def get_next_meeting_date(cls, from_date=None):
        """
        This is a utility to calculate the date of the next meeting after
        `from_date`. The `from_date` defaults to today if not specified.
        """

        if from_date is None:
            from_date = date.today()

        return from_date + timedelta(
            days=7 + (settings.MEETING_DAY - from_date.weekday()) % -7
        )

    @classmethod
    def rotate_next_meeting(cls):
        """
        Generate the coming meeting on the specified `MEETING_DAY` and add
        `PresentHistory` for that meeting.
        return: Next coming `MeetingHistory`.
        """

        today          = date.today()
        future_meeting = cls.objects.filter(date__gt=today)[:1]
        if future_meeting:
            # The future meeting is already generated. Return it directly
            # instead of generating another one.
            return future_meeting[0]

        # Find out the date to hold the new meeting, skipping those dates
        # scheduled to skip meetings.
        next_meeting_day = cls.get_next_meeting_date(from_date=today)
        while MeetingSkip.objects.filter(date=next_meeting_day).exists():
            next_meeting_day += timedelta(days=7)

        # Look up previous meeting and rotate presenters for this meeting.
        last_meeting = cls.objects.all()[0]
        next_rotation1 = last_meeting.last_rotation.get_after()
        next_rotation2 = next_rotation1.get_after()

        # Create the meeting.
        next_meeting = cls.objects.create(
            date          = next_meeting_day,
            last_rotation = next_rotation2,
        )

        # Create presenters for the meeting.
        for presenter in (next_rotation1, next_rotation2):
            manager = presenter.presenter.presenthistory_set
            past = manager.filter(is_specially_arranged=False)

            manager.create(
                meeting=next_meeting,
                present_type=past[0].another_type if past.count() > 0 else PresentHistory.DEFAULT_TYPE,
            )

        # Create default attendance status for the meeting.
        MeetingAttendance.objects.bulk_create([
            MeetingAttendance(
                meeting=next_meeting,
                member=expected.member,
                status=MeetingAttendance.PRESENT_ON_TIME,
            )
            for expected in ExpectedAttendance.objects.all()
        ])

        return next_meeting


class MeetingSkip(models.Model):
    date   = models.DateField()
    reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['date']


class PresentHistory(models.Model):
    PAPER_PRESENTATION = "PAPER"
    PROGRESS_REPORT    = "PROGRESS"
    OTHER              = "OTHER"
    type_choices = (
        (PAPER_PRESENTATION, "Paper presentation"),
        (PROGRESS_REPORT,    "Progress report"),
        (OTHER,              "Other"),
    )
    DEFAULT_TYPE = PROGRESS_REPORT

    presenter    = models.ForeignKey('website.Member', models.SET_NULL, null=True)
    meeting      = models.ForeignKey('MeetingHistory', models.PROTECT)
    present_type = models.CharField(max_length=10, choices=type_choices)
    content      = models.TextField(blank=True)
    is_specially_arranged = models.BooleanField(default=False)

    class Meta:
        ordering = ['meeting']

    def __unicode__(self):
        meeting = unicode(self.meeting.date) if self.meeting else 'Unknown Meeting'
        presenter = unicode(self.presenter) if self.presenter else 'Unknown Presenter'

        return "%s (%s): %s" % (
            presenter,
            meeting,
            self.get_present_type_display()
        )

    def save(self, *args, **kwargs):
        ret = super(PresentHistory, self).save(*args, **kwargs)
        async(sync_meeting_with_gcal, self.meeting)
        return ret

    def delete(self, *args, **kwargs):
        ret = super(PresentHistory, self).delete(*args, **kwargs)
        async(sync_meeting_with_gcal, self.meeting)
        return ret

    @property
    def another_type(self):
        if self.present_type == self.PAPER_PRESENTATION:
            return self.PROGRESS_REPORT
        elif self.present_type == self.PROGRESS_REPORT:
            return self.PAPER_PRESENTATION
        else:
            raise ValueError('Can only exchange "progress report" and "paper presentation".')


class ExpectedAttendance(models.Model):
    """
    The person who is expected to attend each meeting.
    """

    member = models.OneToOneField('website.Member', models.CASCADE)

    def __unicode__(self):
        return unicode(self.member)


class MeetingAttendance(models.Model):
    """
    The status each member attending each meeting.
    """

    PRESENT_ON_TIME = 'ONTIME'
    ON_BUSINESS     = 'BUSINESS'
    LATE            = 'LATE'
    LEAVE_BEFORE    = 'LEAVE_BEFORE'
    LEAVE_AFTER     = 'LEAVE_AFTER'
    ABSENT          = 'ABSENT'
    status_choices = (
        (PRESENT_ON_TIME, 'present on time'),
        (ON_BUSINESS, 'on business'),
        (LATE, 'late'),
        (LEAVE_BEFORE, 'leave in advance'),
        (LEAVE_AFTER, 'leave afterwards'),
        (ABSENT, 'absent'),
    )

    meeting = models.ForeignKey('MeetingHistory', models.CASCADE)
    member  = models.ForeignKey('website.Member', models.CASCADE)
    status  = models.CharField(max_length=15, choices=status_choices)
    reason  = models.TextField(blank=True)

    class Meta:
        unique_together = ('meeting', 'member')

    def save(self, *args, **kwargs):
        ret = super(MeetingAttendance, self).save(*args, **kwargs)
        async(sync_meeting_with_gcal, self.meeting)
        return ret

    def delete(self, *args, **kwargs):
        ret = super(MeetingAttendance, self).delete(*args, **kwargs)
        async(sync_meeting_with_gcal, self.meeting)
        return ret

    def get_is_present(self):
        return self.status in (self.PRESENT_ON_TIME, self.LATE)
