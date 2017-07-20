from django.views.generic import TemplateView, ListView, DetailView, FormView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse
from . import models, forms

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


class PublicationImportView(UserPassesTestMixin, FormView):
    template_name = 'website/publication-import.html'
    form_class = forms.PublicationImportForm

    def get_success_url(self):
        return reverse('website:publications')

    def form_valid(self, form):
        add_count = 0

        for keyword in form.cleaned_data['keywords'].split('\n'):
            pub = models.Publication.get_from_keyword(keyword)

            if pub is not None:
                pub.save()
                add_count += 1
            else:
                print 'Publication for keyword "%s" not found.' % keyword

        print add_count, 'publications imported.'
        return super(PublicationImportView, self).form_valid(form)

    def test_func(self):
        return self.request.user.is_staff


class ActivityListView(ListView):
    model = models.Activity
    template_name = 'website/activity-list.html'


class ActivityDetailView(DetailView):
    model = models.Activity
    template_name = 'website/activity-detail.html'
