from __future__ import unicode_literals

from django.db import models
from django.conf import settings
from django.urls import reverse
from datetime import date, timedelta

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


class MeetingHistory(models.Model):
    """
    The history for past meetings and one coming meeting.
    """

    PAPER_PRESENTATION = "PAPER"
    PROGRESS_REPORT    = "PROGRESS"
    type_choices = (
        (PAPER_PRESENTATION, "Paper presentation"),
        (PROGRESS_REPORT,    "Progress report"),
    )

    date          = models.DateField(unique=True)
    present_type  = models.CharField(max_length=10, choices=type_choices)
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

    class Meta:
        ordering = ['-date']

    def __unicode__(self):
        return "%s %s" % (unicode(self.date), self.get_present_type_display())

    def get_absolute_url(self):
        return reverse('meeting:detail', args=[self.date])

    def not_yet_happened(self):
        return self.date > date.today()

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

        # Find out the type the new meeting shall be and rotate presenters
        # for this meeting.
        last_meeting_of_same_type = cls.objects.all()[1:2][0]
        next_rotation1 = last_meeting_of_same_type.last_rotation.get_after()
        next_rotation2 = next_rotation1.get_after()

        # Create the meeting.
        next_meeting = cls.objects.create(
            date          = next_meeting_day,
            present_type  = last_meeting_of_same_type.present_type,
            last_rotation = next_rotation2,
        )

        # Create presenters for the meeting.
        for presenter in (next_rotation1, next_rotation2):
            PresentHistory.objects.create(
                presenter = presenter.presenter,
                meeting   = next_meeting,
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
    presenter = models.ForeignKey('website.Member', models.SET_NULL, null=True)
    meeting   = models.ForeignKey('MeetingHistory', models.SET_NULL, null=True)
    content   = models.TextField(blank=True)

    class Meta:
        ordering = ['meeting']

    def __unicode__(self):
        return "%s: %s" % (unicode(self.meeting), unicode(self.presenter))


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

    def get_is_present(self):
        return self.status in (self.PRESENT_ON_TIME, self.LATE)
