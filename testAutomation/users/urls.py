from django.conf.urls import url

from .views import (
    AddUserView,
    DeleteUserView,
    DirectoryView,
    EditOrganizationView,
    EditProfileView,
    EditUserView,
    OrganizationDetailView,
    OrganizationView,
    RegisterView,
    RegistrationConfirmationView,
    UserPasswordChangeView
)

urlpatterns = [
    url(r'^register/$', RegisterView.as_view(), name='register'),
    url(r'^organization/$', OrganizationView.as_view(), name='organization'),
    url(r'^organization/adduser/$', AddUserView.as_view(), name='add-user'),
    url(r'^directory/$', DirectoryView.as_view(), name='directory'),
    url(
        r'^directory/(?P<pk>\d+)$',
        OrganizationDetailView.as_view(), name='organization-detail'
    ),
    url(
        r'^organization/edituser/(?P<pk>\d+)/?$',
        EditUserView.as_view(), name='edit-user'
    ),
    url(
        r'^organization/deleteuser/(?P<pk>\d+)/?$',
        DeleteUserView.as_view(), name='delete-user'
    ),
    url(
        r'^organization/edit/$',
        EditOrganizationView.as_view(),
        name='edit-organization'
    ),
    url(r'^profile/edit/$', EditProfileView.as_view(), name='edit-profile'),
    url(r'^change/password/$', UserPasswordChangeView.as_view(), name='change-password'),
    url(
        r'^registration/confirmation/$',
        RegistrationConfirmationView.as_view(), name='registration-confirm'
    )
]
