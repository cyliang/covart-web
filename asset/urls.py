from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.AssetTableView.as_view(), name='all'),
]

app_name = 'asset'
