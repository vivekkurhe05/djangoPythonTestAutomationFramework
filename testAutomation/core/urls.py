from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from . import views

urlpatterns = [
    url(r'', include('rewrite_external_links.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', views.Landing.as_view(), name='landing'),
    url(r'^home/', views.Home.as_view(), name='home'),
    url(r'^faq/', views.FAQ.as_view(), name='faq'),
    url(r'^aboutus/', views.AboutUs.as_view(), name='aboutus'),
    url(r'^privacy/', views.PrivacyPolicy.as_view(), name='privacy'),
    url(r'', include('incuna_auth.urls')),
    url(r'', include('users.urls')),
    url(r'^survey/', include('surveys.urls')),
    url(r'^document/', include('documents.urls')),
    url(r'^subscription/', include('subscriptions.urls')),
    url(r'', include('user_management.ui.urls')),
    url(r'', include('feincms.contrib.preview.urls')),
    url(r'', include('feincms.urls')),
]

if settings.DEBUG:  # pragma: nocover
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
