from __future__ import unicode_literals

from django.db import models

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
    picture       = models.ImageField(blank=True)
    join_date     = models.DateField(auto_now_add=True, editable=True)
    graduate_date = models.DateField(null=True, blank=True)
