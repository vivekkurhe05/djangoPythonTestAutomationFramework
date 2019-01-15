from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from rolepermissions.checkers import has_role

from documents.models import Document
from surveys.models import Survey
from users.models import Invitation

from .mixins import AppMixin


class Home(LoginRequiredMixin, AppMixin, TemplateView):
    template_name = 'home.html'
    sidebar_item = 'dashboard'
    sidebar_item = 'dashboard'
    page_title = 'Dashboard'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        organisation = self.request.user.organisation
        surveys = Survey.objects.filter(
            is_active=True,
        ).with_latest_response_progress(
            organisation
        )

        invites = Invitation.objects.filter(
            grantee=organisation,
            accepted=False,
        )

        documents_count = Document.objects.filter(organisation=organisation).count()
        can_manage_invites = has_role(self.request.user, ['admin', 'manager'])
        context.update({
            'can_manage_invites': can_manage_invites,
            'surveys': surveys,
            'invites': invites,
            'documents_count': documents_count
        })

        return context


class Landing(TemplateView):
    template_name = 'landing.html'

    def get(self, request, *args, **kwargs):
        if(self.request.user.is_authenticated()):
            return redirect('/home')
        return render(request, self.template_name)


class FAQ(LoginRequiredMixin, AppMixin, TemplateView):
    template_name = 'faq.html'
    sidebar_item = 'faq'
    page_title = 'Help & FAQ'


class AboutUs(TemplateView):
    template_name = 'about_us.html'


class PrivacyPolicy(TemplateView):
    template_name = 'privacy_policy.html'
