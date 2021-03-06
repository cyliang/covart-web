from django.views.generic import TemplateView, ListView, DetailView, FormView, UpdateView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.urls import reverse
from django_tables2 import SingleTableMixin
from django_filters.views import FilterMixin
from . import models, forms
from meeting import tables as meeting_tables, filters as meeting_filters, models as meeting_models

class IndexView(TemplateView):
    template_name = 'website/index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)

        context['menu_attached'] = True
        context['professor'] = models.Member.objects.get(identity=models.Member.ADVISOR)
        context['activities'] = models.Activity.objects.all()[:4]
        context['publications'] = models.Publication.objects.filter(hidden=False)[:5]

        return context


class MemberListView(ListView):
    model = models.Member
    template_name = 'website/member-list.html'


class MemberDetailView(FilterMixin, SingleTableMixin, DetailView):
    model = models.Member
    template_name = 'website/member-detail.html'
    table_class = meeting_tables.MemberPresentHistoryTable
    filterset_class = meeting_filters.AttendanceStatusFilter

    def get_template_names(self):
        if self.object.identity == self.model.ADVISOR:
            return 'website/advisor.html'
        return super(MemberDetailView, self).get_template_names()

    def get_object(self):
        if self.request.resolver_match.view_name == 'website:advisor':
            return self.model.objects.get(identity=self.model.ADVISOR)
        return super(MemberDetailView, self).get_object()

    def get_table_data(self):
        """
        Return the table data for showing present history of this member.
        """
        return self.object.presenthistory_set.all()

    def get_filterset_kwargs(self, filterset_class):
        """
        Return the filterset data for showing the attendance status of this member.
        """
        return {
            'data': self.request.GET or None,
            'request': self.request,
            'queryset': self.object.meetingattendance_set.all(),
        }

    def get_context_data(self, **kwargs):
        """
        Add the filterset and the filtered attendance data into the context.
        """
        context = super(MemberDetailView, self).get_context_data(**kwargs)

        # Special look for the advisor.
        if self.object.identity == self.model.ADVISOR:
            context['menu_attached'] = True
            context['publications'] = models.Publication.objects.filter(hidden=False)[:5]

        filterset = self.get_filterset(self.get_filterset_class())
        MeetingAttendance = meeting_models.MeetingAttendance

        expected = filterset.qs.exclude(status=MeetingAttendance.ON_BUSINESS).count()
        on_time = filterset.qs.filter(status=MeetingAttendance.PRESENT_ON_TIME).count()
        late = filterset.qs.filter(status=MeetingAttendance.LATE).count()
        absent = expected - on_time - late

        context['filter'] = filterset
        context['attendance'] = [
            {
                'label': 'On time',
                'num': on_time,
                'percentage': on_time * 100 / expected,
            },
            {
                'label': 'Late',
                'num': late,
                'percentage': late * 100 / expected,
            },
            {
                'label': 'Absent or leave',
                'num': absent,
                'percentage': absent * 100 / expected,
            },
        ] if expected > 0 else None

        return context


class MemberUpdateView(LoginRequiredMixin, UpdateView):
    model = models.Member
    template_name = 'website/member-update.html'
    form_class = forms.MemberUpdateForm

    def get_object(self):
        return self.request.user.member

    def form_valid(self, form):
        if form.cleaned_data['del_pic']:
            self.object.picture = ''

        return super(MemberUpdateView, self).form_valid(form)


class PublicationListView(ListView):
    model = models.Publication
    template_name = 'website/publication-list.html'


class PublicationDetailView(DetailView):
    model = models.Publication
    template_name = 'website/publication-detail.html'


class ActivityListView(ListView):
    model = models.Activity
    template_name = 'website/activity-list.html'


class ActivityDetailView(DetailView):
    model = models.Activity
    template_name = 'website/activity-detail.html'

    def get_context_data(self, **kwargs):
        context = super(ActivityDetailView, self).get_context_data(**kwargs)
        context['object_list'] = self.model.objects.all()[:10]
        return context


class LinkListView(LoginRequiredMixin, ListView):
    model = models.InternalLink
    template_name = 'website/link-list.html'
