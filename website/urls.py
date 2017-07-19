from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^publications$', views.PublicationListView.as_view(), name='publications'),
]

app_name = 'website'
