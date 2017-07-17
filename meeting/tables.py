import django_tables2 as tables
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
