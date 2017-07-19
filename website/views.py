from django.views.generic import TemplateView, ListView, DetailView
from . import models

class IndexView(TemplateView):
    template_name = 'website/index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)

        context['activities'] = models.Activity.objects.all()[:4]
        context['publications'] = models.Publication.objects.all()[:5]

        return context


class MemberListView(ListView):
    model = models.Member
    template_name = 'website/member-list.html'


class PublicationListView(ListView):
    model = models.Publication
    template_name = 'website/publication-list.html'


class ActivityListView(ListView):
    model = models.Activity
    template_name = 'website/activity-list.html'


class ActivityDetailView(DetailView):
    model = models.Activity
    template_name = 'website/activity-detail.html'
