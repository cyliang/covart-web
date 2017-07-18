import django_tables2 as tables
from django_tables2 import A
from django.urls import reverse
from . import models

class ScheduleTable(tables.Table):
    date = tables.DateColumn(verbose_name='Scheduled Date')
    present_type = tables.Column(verbose_name='Type')
    presenter = tables.Column(verbose_name='Presenter')

    class Meta:
        orderable = False
        attrs = {'class': 'ts table'}
        row_attrs = {
            'class': lambda record: 'indicated ' + (
                'info' if record['present_type'] == models.MeetingHistory.type_choices[0][1]
                else 'negative'
            )
        }


class HistoryTable(tables.Table):
    date = tables.DateColumn(accessor='meeting.date')
    present_type = tables.Column(verbose_name='Type', accessor='meeting.get_present_type_display')
    presenter = tables.Column()
    content = tables.Column()

    class Meta:
        orderable = False
        attrs = {'class': 'ts selectable fixed single line table'}
        row_attrs = {
            'class': lambda record: 'clickable indicated ' + (
                'info' if record.meeting.present_type == models.MeetingHistory.type_choices[0][0]
                else 'negative'
            ),
            'onclick': lambda record: "window.location='%s';" % reverse(
                'meeting:detail', args=[record.meeting.date]
            ),
        }
