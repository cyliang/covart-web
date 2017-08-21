from __future__ import unicode_literals

from django.db import models
from django.utils.text import slugify
from django.utils.timezone import now
from django.conf import settings
from django.urls import reverse
from time import time
import requests

def member_picture_path(instance, filename):
    return 'member_pictures/%d-%d-%s' % (
        instance.pk, int(time()), filename
    )

class Member(models.Model):
    ADVISOR          = "aADVISOR"
    PHD_STUDENT      = "bPHD"
    MS_STUDENT       = "cMS"
    INTERN_STUDENT   = "dINTERN"
    ASSISTANT        = "eASSISTANT"
    students         = (PHD_STUDENT, MS_STUDENT, INTERN_STUDENT)
    identity_choices = (
        (ADVISOR,        "Advisor"),
        (MS_STUDENT,     "Master"),
        (PHD_STUDENT,    "PhD"),
        (INTERN_STUDENT, "Intern"),
        (ASSISTANT,      "Assitant"),
    )

    name          = models.CharField(max_length=255)
    identity      = models.CharField(max_length=10, choices=identity_choices, default=MS_STUDENT)
    email         = models.EmailField(blank=True)
    picture       = models.ImageField(blank=True, upload_to=member_picture_path)
    join_date     = models.DateField(default=now)
    graduate_date = models.DateField(null=True, blank=True)
    thesis        = models.CharField(max_length=255, blank=True)
    user          = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)

    def graduate_year(self):
        return self.graduate_date.year if self.graduate_date else None

    def graduated(self):
        return bool(self.graduate_date)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('website:member-detail', kwargs={
            'pk': self.pk,
            'name': self.name,
        })

    def get_internal_email(self):
        if not self.user:
            return None

        email = self.user.email
        social = self.user.social_auth.filter(provider='google-oauth2')
        if not email and social.exists():
            email = social[0].uid

        return email


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

    def get_absolute_url(self):
        return reverse('website:activity-detail', args=[self.slug])


class Publication(models.Model):
    CONFERENCE  = 'Conference and Workshop Papers'
    JOURNAL     = 'Journal Articles'
    TECH_REPORT = 'Technical Report'
    PATENT      = 'Patent'
    OTHER       = 'Other'
    TYPE_CHOICE = (
        (CONFERENCE, CONFERENCE),
        (JOURNAL, JOURNAL),
        (TECH_REPORT, TECH_REPORT),
        (PATENT, PATENT),
        (OTHER, OTHER),
    )

    authors    = models.CharField(max_length=255)
    title      = models.CharField(max_length=255)
    slug       = models.SlugField()
    paper_type = models.CharField(max_length=255, choices=TYPE_CHOICE)
    year       = models.IntegerField()
    venue      = models.CharField(max_length=255)
    pages      = models.CharField(max_length=255, blank=True)
    dblp_key   = models.CharField(max_length=255, blank=True)
    best_paper = models.BooleanField(default=False)
    hidden     = models.BooleanField(default=False)

    class Meta:
        ordering = ['-year']

    def __unicode__(self):
        return self.title

    @classmethod
    def get_from_keyword(cls, keyword):
        r = requests.get('http://dblp.uni-trier.de/search/publ/api', {
            'q': keyword,
            'h': 1000,
            'format': 'json'
        })

        try:
            result = r.json()['result']
        except ValueError:
            pass
        finally:
            if result['status']['@code'] == '200' and (result['hits']['@total'] == '1'
                    or int(result['hits']['@total']) > 0 and 'Wei-Chung Hsu' in result['hits']['hit'][0]['info']['authors']['author']):
                info = result['hits']['hit'][0]['info']

                obj = cls()
                obj.authors = ', '.join(info['authors']['author'])
                obj.title = info['title']
                obj.venue = info['venue']
                obj.pages = info.get('pages', '')
                obj.year = int(info['year'])
                obj.paper_type = info['type']
                obj.dblp_key = info['key']
                obj.slug = slugify(obj.title)[:50]

                return obj

        return None


class InternalLink(models.Model):
    title       = models.CharField(max_length=255)
    help_text   = models.CharField(max_length=255, blank=True)
    link        = models.URLField()
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-update_time']

    def __unicode__(self):
        return self.title
