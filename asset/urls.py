from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.AssetTableView.as_view(), name='all'),
    url(r'^(?P<slug>.+)$', views.AssetDetailView.as_view(), name='detail'),
]

app_name = 'asset'
