from django.views.generic import DetailView
from django_tables2 import SingleTableView
from datetime import timedelta
from . import tables, models

class ScheduleView(SingleTableView):
    """
    Show the upcoming scheduled meeting specially and other future scheduled
    meetings in a table.
    """
    table_class = tables.ScheduleTable
    template_name = 'meeting/schedule.html'

    def get_queryset(self):
        """
        Generate data (all future meetings) for the table.
        Since only the exact next meeting is in the database, other future
        meetings are calculated in the runtime.
        """
        next_meeting, prev_meeting = models.MeetingHistory.objects.all()[0:2]

        # Get next meeting
        result = [
            {
                'date': next_meeting.date,
                'present_type': next_meeting.get_present_type_display(),
                'presenter': presenter
            }
            for presenter in next_meeting.presenters.all()
        ]

        # Get other future meetings.
        type1, type2 = [
            [m.get_present_type_display(), m.last_rotation]
            for m in (prev_meeting, next_meeting)
        ]
        date = next_meeting.date
        for i in range(5):
            for t in (type1, type2):
                next_rotation1 = t[1].get_after()
                next_rotation2 = next_rotation1.get_after()
                t[1] = next_rotation2

                date += timedelta(days=7)
                while models.MeetingSkip.objects.filter(date=date).exists():
                    skip = models.MeetingSkip.objects.get(date=date)
                    result += [{
                        'date': date,
                        'postponed': skip.reason,
                    }]

                    date += timedelta(days=7)

                for r in (next_rotation1, next_rotation2):
                    result += [{
                        'date': date,
                        'present_type': t[0],
                        'presenter': r.presenter
                    }]

        return result

    def get_context_data(self, **kwargs):
        """
        Append data specially for the upcoming meeting, which has information
        already stored in the database.
        """
        context = super(ScheduleView, self).get_context_data(**kwargs)

        context['upcoming'] = models.MeetingHistory.objects.all()[0]

        return context

class HistoryView(SingleTableView):
    table_class = tables.HistoryTable
    template_name = 'meeting/history.html'

    def get_queryset(self):
        return models.PresentHistory.objects.order_by('meeting')[2:]


class MeetingDetailView(DetailView):
    model = models.MeetingHistory
    template_name = 'meeting/detail.html'
    slug_field = 'date'

