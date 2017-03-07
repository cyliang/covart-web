from __future__ import unicode_literals

from django.db import models

class PresentRotation(models.Model):
    order     = models.IntegerField(unique=True)
    presenter = models.OneToOneField('website.Member', models.CASCADE)
    join_date = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return "%d: %s" % (self.order, self.presenter)


class MeetingHistory(models.Model):
    PAPER_PRESENTATION = "PAPER"
    PROGRESS_REPORT    = "PROGRESS"
    type_choices = (
        (PAPER_PRESENTATION, "Paper presentation"),
        (PROGRESS_REPORT,    "Progress report"),
    )

    date          = models.DateField(unique=True)
    present_type  = models.CharField(max_length=10, choices=type_choices)
    last_rotation = models.ForeignKey('PresentRotation', models.SET_NULL, null=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return "%s %s" % (str(self.date), self.get_present_type_display())


class PresentHistory(models.Model):
    presenter = models.ForeignKey('website.Member', models.SET_NULL, null=True)
    meeting   = models.ForeignKey('MeetingHistory', models.SET_NULL, null=True)
    content   = models.TextField(blank=True)

    class Meta:
        ordering = ['meeting']

    def __str__(self):
        return "%s: %s" % (str(self.meeting), str(self.presenter))
