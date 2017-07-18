import django_tables2 as tables
from django.utils.text import Truncator
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
        attrs = {'class': 'ts fixed single line table'}
        row_attrs = {
            'class': lambda record: 'indicated ' + (
                'info' if record.meeting.present_type == models.MeetingHistory.type_choices[0][0]
                else 'negative'
            )
        }
