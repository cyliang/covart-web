from django.views.generic import TemplateView
from . import models

class IndexView(TemplateView):
    template_name = 'website/index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)

        context['activities'] = models.Activity.objects.all()[:4]

        return context
