from django.conf.urls import url

from .views import DocumentEdit, DocumentHome

urlpatterns = [
    url(r'^$', DocumentHome.as_view(), name='document-home'),
    url(r'^edit/(?P<pk>\d+)/?$', DocumentEdit.as_view(), name='document-edit'),
]
