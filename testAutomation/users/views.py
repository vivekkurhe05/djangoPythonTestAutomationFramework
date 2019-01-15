from collections import OrderedDict

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import PasswordChangeView
from django.core import signing
from django.core.urlresolvers import reverse_lazy
from django.db import models
from django.shortcuts import redirect
from django.views.generic import (
    DeleteView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView
)
from rolepermissions.checkers import has_role
from rolepermissions.roles import assign_role, clear_roles, get_user_roles

from core.mixins import AjaxMixin, AppMixin
from surveys.models import SurveyResponse
from users.models import Invitation, Organisation, OrganisationType, User
from .forms import (
    AddUserForm,
    OrganisationForm,
    OrganisationRegisterForm,
    PasswordChangeForm,
    ProfileForm,
    RegisterForm
)


class OrganizationMixin(LoginRequiredMixin, UserPassesTestMixin, AppMixin):
    sidebar_section = 'settings'
    sidebar_item = 'users'
    page_title = 'Organization & users'


class ProfileMixin(LoginRequiredMixin, AppMixin):
    sidebar_section = 'settings'
    sidebar_item = 'profile'
    page_title = 'My profile'


class RegisterView(FormView):
    form_class = RegisterForm

    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'

    def get(self, request, *args, **kwargs):
        self.encrypted_token = self.request.GET.get('token', '')

        user_form = RegisterForm()
        org_form = OrganisationRegisterForm()

        context = self.get_context_data(
            user_form=user_form,
            organisation_form=org_form,
            token=self.encrypted_token
        )
        return self.render_to_response(context)

    def form_invalid(self, user_form, org_form, **kwargs):
        messages.warning(
            self.request, 'Registration Failed, please correct the form',
            extra_tags='show-icon'
        )
        context = self.get_context_data(
            user_form=user_form,
            organisation_form=org_form
        )
        return self.render_to_response(context)

    def form_valid(self, user_form, org_form, **kwargs):

        encrypted_token = self.request.POST.get('token')
        is_verification_required = True

        if(encrypted_token != ''):
            try:
                decrypted_token = signing.loads(encrypted_token)
            except signing.BadSignature:
                messages.warning(
                    self.request, 'Registration Failed, Invalid token',
                    extra_tags='show-icon'
                )
                context = self.get_context_data(
                    user_form=user_form,
                    organisation_form=org_form
                )
                return self.render_to_response(context)

            saved_organisation = org_form.save()
            user_object = user_form.save(commit=False)
            user_object.organisation = saved_organisation

            try:
                user_invitation = Invitation.objects.get(
                    id=decrypted_token,
                    grantee=None,
                    accepted=False,
                )
            except Invitation.DoesNotExist:
                messages.warning(
                    self.request, 'Registration Failed, Invalid token',
                    extra_tags='show-icon'
                )
                context = self.get_context_data(
                    user_form=user_form,
                    organisation_form=org_form
                )
                return self.render_to_response(context)

            if(user_form.instance.email == user_invitation.grantee_email):
                is_verification_required = False

            user_invitation.grantee = user_object.organisation
            user_invitation.save()
        else:
            saved_organisation = org_form.save()
            user_object = user_form.save(commit=False)
            user_object.organisation = saved_organisation

            invitations = Invitation.objects.filter(
                grantee_email=user_form.instance.email,
                grantee=None,
                accepted=False,
            )
            invitations.update(grantee=saved_organisation)

        saved_organisation.save()

        if(is_verification_required):
            user_object.save()
            user_object.send_validation_email()
            assign_role(user_object, 'admin')
            return redirect(reverse_lazy('registration-confirm'))
        else:
            user_object.is_active = True
            user_object.email_verified = True
            user_object.save()
            assign_role(user_object, 'admin')
            messages.success(self.request, (
                'Thanks for signing up. Please login'
            ), extra_tags='show-icon')
            return redirect(reverse_lazy('login'))

    def post(self, request, *args, **kwargs):
        user_form = RegisterForm(self.request.POST, self.request.FILES)
        organisation_form = OrganisationRegisterForm(
            self.request.POST,
            self.request.FILES,
        )

        if(user_form.is_valid() and organisation_form.is_valid()):
            return self.form_valid(user_form, organisation_form, **kwargs)
        else:
            return self.form_invalid(user_form, organisation_form, **kwargs)


class RegistrationConfirmationView(TemplateView):
    template_name = 'registration/confirmation.html'


class OrganizationView(OrganizationMixin, TemplateView):
    template_name = 'organization/organization.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        users = User.objects.filter(organisation=self.request.user.organisation)
        context.update({
            'user_list': users,
            'current_user': self.request.user,
            'organisation': self.request.user.organisation
        })
        return context

    def test_func(self):
        return has_role(self.request.user, ['admin'])


class AddUserView(OrganizationMixin, FormView):
    template_name = 'organization/add_user.html'
    form_class = AddUserForm
    success_url = reverse_lazy('organization')

    def test_func(self):
        return has_role(self.request.user, ['admin'])

    def form_invalid(self, user_form):
        messages.warning(
            self.request, 'Add user failed, please correct the form',
            extra_tags='show-icon'
        )
        return super().form_invalid(user_form)

    def form_valid(self, form):
        form.instance.organisation = self.request.user.organisation
        form.instance.is_active = True
        form.instance.email_verified = True
        user_object = form.save()

        user_type = form.cleaned_data['user_type']
        assign_role(user_object, user_type)
        user_object.send_welcome_invite()
        messages.success(
            self.request, 'User added successfully',
            extra_tags='show-icon'
        )
        return super().form_valid(form)


class FetchUserMixin():
    def get_queryset(self):
        return super().get_queryset().filter(
            organisation=self.request.user.organisation
        ).exclude(pk=self.request.user.pk)


class EditUserView(OrganizationMixin, FetchUserMixin, UpdateView):
    template_name = 'organization/edit_user.html'
    form_class = AddUserForm
    success_url = reverse_lazy('organization')
    model = User

    def test_func(self):
        return has_role(self.request.user, ['admin'])

    def _get_permission(self, user):
        try:
            return get_user_roles(user)[0].get_name()
        except IndexError:
            return AddUserForm.USER_TYPE_CHOICES[-1][0]

    def form_invalid(self, form, **kwargs):
        messages.warning(
            self.request, 'User update failed, please correct the form',
            extra_tags='show-icon'
        )
        return super().form_invalid(form)

    def form_valid(self, form):
        user_type = form.cleaned_data['user_type']

        clear_roles(user=self.object)
        assign_role(self.object, user_type)

        messages.success(
            self.request, 'User updated successfully',
            extra_tags='show-icon'
        )
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user = self.object
        user_type = self._get_permission(user)

        kwargs['initial'] = {
            'user_type': user_type
        }
        return kwargs


class DeleteUserView(
    AjaxMixin,
    LoginRequiredMixin,
    UserPassesTestMixin,
    FetchUserMixin,
    DeleteView
):
    template_name = 'organization/delete_user_modal.html'
    success_url = reverse_lazy('organization')
    context_object_name = 'user'
    model = User

    def test_func(self):
        return has_role(self.request.user, ['admin'])

    def get_queryset(self):
        return super().get_queryset().exclude(pk=self.request.user.pk)

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.success(self.request, (
            'User successfully deleted'
        ), extra_tags='show-icon')
        return response


class EditOrganizationView(OrganizationMixin, UpdateView):
    template_name = 'organization/edit_organization.html'
    form_class = OrganisationForm
    success_url = reverse_lazy('organization')

    def test_func(self):
        return has_role(self.request.user, ['admin'])

    def get_object(self, queryset=None):
        return self.request.user.organisation

    def form_invalid(self, form, **kwargs):
        messages.warning(
            self.request, 'Organization update failed, please correct the form',
            extra_tags='show-icon'
        )
        return super().form_invalid(form)

    def form_valid(self, form):
        messages.success(
            self.request, 'Organization updated successfully',
            extra_tags='show-icon'
        )
        return super().form_valid(form)


class DirectoryMixin(LoginRequiredMixin, AppMixin):
    sidebar_item = 'directory'
    page_title = 'Directory'

    def _get_sidebar(self):
        org_types = OrganisationType.objects.annotate(
            value=models.Count('organisation'),
        ).values('pk', 'name', 'value')

        sidebar = OrderedDict({'total': {
            'name': 'All',
            'value': Organisation.objects.count(),
        }})

        sidebar.update({
            org_type['pk']: org_type
            for org_type in org_types
        })

        return sidebar

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        sidebar = self._get_sidebar()
        context.update({
            'directory_sidebar': sidebar
        })

        return context


class DirectoryView(DirectoryMixin, ListView):
    template_name = 'organization/directory.html'
    model = Organisation

    def get_queryset(self):
        return super().get_queryset().prefetch_related('types')


class OrganizationDetailView(DirectoryMixin, DetailView):
    template_name = 'organization/organization_detail.html'
    model = Organisation

    def get_queryset(self):
        return super().get_queryset().select_related('country')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        organisation = context['object']
        responses = SurveyResponse.objects.filter(
            organisation=organisation,
            submitted__isnull=False,
        ).select_related('survey')
        context.update({
            'responses': responses
        })
        return context


class EditProfileView(ProfileMixin, UpdateView):
    template_name = 'user_management/profile_edit.html'
    form_class = ProfileForm
    success_url = reverse_lazy('edit-profile')

    def get_object(self, queryset=None):
        return self.request.user

    def form_invalid(self, user_form):
        messages.warning(
            self.request, 'Edit profile failed, please correct the form',
            extra_tags='show-icon'
        )
        return super().form_invalid(user_form)

    def form_valid(self, form):
        messages.success(
            self.request, 'User profile updated successfully',
            extra_tags='show-icon'
        )
        return super().form_valid(form)


class UserPasswordChangeView(ProfileMixin, PasswordChangeView):
    template_name = 'registration/password_change_form.html'
    form_class = PasswordChangeForm

    def form_valid(self, form):
        super().form_valid(form)
        messages.success(
            self.request, 'Password has been updated successfully',
            extra_tags='show-icon'
        )
        return redirect(reverse_lazy('edit-profile'))

    def form_invalid(self, form):
        messages.warning(
            self.request, 'Please correct the form errors',
            extra_tags='show-icon'
        )
        return super().form_invalid(form)
