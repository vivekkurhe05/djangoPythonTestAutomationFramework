from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.SubscriptionListView.as_view(), name='subscription'),
    url(r'^order/$', views.OrderView.as_view(), name='subscription-order'),
    url(r'^order/history$', views.OrderHistoryView.as_view(), name='order-history'),
    url(
        r'^order/history/(?P<pk>\d+)$',
        views.OrderDetailsView.as_view(),
        name='order-details',
    ),
]
