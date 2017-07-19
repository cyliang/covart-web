from __future__ import unicode_literals

from django.db import models
from time import time

def member_picture_path(instance, filename):
    return 'member_pictures/%d-%d-%s' % (
        instance.pk, int(time()), filename
    )

class Member(models.Model):
    ADVISOR        = "ADVISOR"
    MS_STUDENT     = "MS"
    PHD_STUDENT    = "PHD"
    INTERN_STUDENT = "INTERN"
    ASSISTANT      = "ASSISTANT"
    identity_choices = (
        (ADVISOR,       "Advisor"),
        (MS_STUDENT,     "MS student"),
        (PHD_STUDENT,    "PhD student"),
        (INTERN_STUDENT, "Intern student"),
        (ASSISTANT,      "Assitant"),
    )

    name          = models.CharField(max_length=255)
    identity      = models.CharField(max_length=10, choices=identity_choices, default=MS_STUDENT)
    email         = models.EmailField(blank=True)
    picture       = models.ImageField(blank=True, upload_to=member_picture_path)
    join_date     = models.DateField(auto_now_add=True, editable=True)
    graduate_date = models.DateField(null=True, blank=True)

    def graduate_year(self):
        return self.graduate_date.year if self.graduate_date else None

    def __unicode__(self):
        return self.name


def activity_picture_path(instance, filename):
    return 'activity_pictures/%s-%d-%s' % (
        instance.slug, int(time()), filename
    )

class Activity(models.Model):
    title     = models.CharField(max_length=255)
    slug      = models.SlugField()
    post_time = models.DateTimeField()
    content   = models.TextField(blank=True)
    picture   = models.ImageField(blank=True, upload_to=activity_picture_path)

    class Meta:
        ordering = ['-post_time']

    def __unicode__(self):
        return self.title


class Publication(models.Model):
    authors    = models.CharField(max_length=255)
    title      = models.CharField(max_length=255)
    slug       = models.SlugField()
    date       = models.DateField()
    at         = models.CharField(max_length=255)
    index      = models.CharField(max_length=255, blank=True)
    best_paper = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date']

    def __unicode__(self):
        return self.title
