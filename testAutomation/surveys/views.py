import xlwt

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models import OuterRef, Prefetch, Q, Subquery
from django.http import Http404, HttpResponse
from django.http.response import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView, ListView, TemplateView, View
from django.views.generic import DeleteView, RedirectView, UpdateView
from rolepermissions.checkers import has_role

from core.mixins import AjaxMixin, AppMixin, PaginationMixin
from users.models import Invitation as InvitationModel

from .forms import (
    InvitationForm,
    SubmitForm,
    SurveyAnswerForm,
    SurveyLevelForm,
)
from .models import (
    get_level_name,
    LEVEL_CHOICES,
    Survey,
    SurveyAnswer,
    SurveyAnswerDocument,
    SurveyQuestion,
    SurveyResponse,
    SurveySection,
)


class SurveyViewMixin:
    """
    Retrieve some kwargs during dispatch() and add structural information to the context.
    """
    def dispatch(self, request, *args, **kwargs):
        self.get_survey_response(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def get_survey_response(self, request, *args, **kwargs):
        """
        Fetch a SurveyResponse object corresponding to the `pk` URL argument. 404 if
        it doesn't exist or the user doesn't match request.user.
        """
        queryset = self.get_survey_queryset(request.user)
        queryset = queryset.select_related('survey')
        self.survey_response = get_object_or_404(queryset, pk=kwargs.pop('pk'))
        self.survey = self.survey_response.survey
        self.level = self.survey_response.level
        return self.survey_response

    def get_survey_queryset(self, user):
        return SurveyResponse.objects.for_user(user)

    def get_context_data(self, **kwargs):
        kwargs.update(
            survey=self.survey,
            level_display=get_level_name(self.level),
        )
        return super().get_context_data(**kwargs)


class InvitesMixin(AppMixin):
    sidebar_item = 'invites'


class AssessmentMixin(AppMixin):
    sidebar_item = 'assessments'


class SurveyStartView(LoginRequiredMixin, RedirectView):
    def get(self, request, *args, **kwargs):
        self.survey = get_object_or_404(Survey, pk=kwargs.pop('pk'), is_active=True)

        responses = SurveyResponse.objects.filter(
            organisation__pk=request.user.organisation_id,
            survey=self.survey,
        )

        self.survey_response = responses.order_by('-modified').first()

        if self.survey_response is None:
            self.survey_response = SurveyResponse.objects.create(
                survey=self.survey,
                organisation=request.user.organisation,
                level=1,
            )

        return super().get(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        first_section = SurveyQuestion.objects.next_section(self.survey)
        if not first_section:
            raise Http404('No Section found')
        return reverse('survey-section', kwargs={
            'pk': self.survey_response.pk,
            'section': first_section,
        })


class SurveyAnswerFormMixin(SurveyViewMixin):
    def get_answer_form_kwargs(self, question):
        return {
            'prefix': 'level_{}_{}'.format(question.level, question.pk),
            'question': question,
            'response': self.survey_response,
        }


class SurveySectionView(
    LoginRequiredMixin,
    AssessmentMixin,
    SurveyAnswerFormMixin,
    UpdateView,
):
    template_name = 'surveys/section.html'
    model = SurveyResponse
    form_class = SurveyLevelForm

    def get_section(self):
        try:
            section_id = self.kwargs['section']
        except KeyError:
            first_question = SurveyQuestion.objects.filter(
                survey=self.survey,
            ).select_related(
                'section__area',
            ).first()
            if first_question is None:
                raise Http404('No SurveySection found')

            return first_question.section
        else:
            qs = SurveySection.objects.select_related('area')
            return get_object_or_404(qs, pk=section_id)

    def get_success_url(self):
        return reverse('survey-section', kwargs={
            'pk': self.object.pk,
            'section': self.section.pk,
        })

    def get_object(self, queryset=None):
        """
        Save self.questions here - after the dispatch variables have been initialised,
        but before we need to use it. We need them on both GET and POST.
        """
        self.section = self.get_section()
        self.questions = SurveyQuestion.objects.for_section(
            survey=self.survey,
            section=self.section,
        ).select_related(
            'section__area',
        ).prefetch_related(
            'options',
        )
        self.answers = SurveyAnswer.objects.filter(
            response=self.survey_response,
        ).prefetch_related(
            'options',
            'documents__document',
        ).order_by(
            'question__level',
            'question__question_number',
        )
        self.answers_lookup = self.answers.by_question()
        return self.survey_response

    def get_summary_url(self):
        return self.object.get_summary_url(self.progress['is_complete'])

    def get_next_url(self):
        section = SurveyQuestion.objects.next_section(
            self.survey,
            self.section,
        )
        if not section:
            return None

        return reverse('survey-section', kwargs={
            'pk': self.object.pk,
            'section': section,
        })

    def get_previous_url(self):
        section = SurveyQuestion.objects.previous_section(
            self.survey,
            self.section,
        )
        if not section:
            return None

        return reverse('survey-section', kwargs={
            'pk': self.object.pk,
            'section': section,
        })

    def get_page_title(self):
        return '{}'.format(
            self.survey.name
        )

    @cached_property
    def progress(self):
        return self.object.get_progress()

    def get_answer_form(self, question):
        answer = self.answers_lookup.get(question.pk)
        kwargs = self.get_answer_form_kwargs(question)
        return SurveyAnswerForm(instance=answer, **kwargs)

    def get_answer_forms(self, level):
        return (
            self.get_answer_form(question)
            for question in self.questions
            if question.level == level
        )

    def get_levels(self):
        return (
            {
                'level': level,
                'label': label,
                'hide': level > self.object.level,
                'forms': self.get_answer_forms(level)
            }
            for level, label in LEVEL_CHOICES
        )

    def get_context_data(self, **kwargs):
        kwargs.update(
            section=self.section,
            levels=self.get_levels(),
            progress=self.progress,
            summary_url=self.get_summary_url(),
            previous_url=self.get_previous_url(),
            next_url=self.get_next_url(),
        )
        return super().get_context_data(**kwargs)


class SurveyAnswerView(
    AjaxMixin,
    LoginRequiredMixin,
    SurveyAnswerFormMixin,
    UpdateView,
):
    model = SurveyAnswer
    form_class = SurveyAnswerForm
    template_name = 'surveys/answer_form.html'

    def get_survey_response(self, request, *args, **kwargs):
        survey_response = super().get_survey_response(request, *args, **kwargs)
        queryset = SurveyQuestion.objects.filter(survey_id=survey_response.survey_id)
        self.question = get_object_or_404(queryset, pk=kwargs.pop('question'))
        return survey_response

    def get_success_url(self):
        return reverse('survey-answer', kwargs={
            'pk': self.survey_response.pk,
            'question': self.question.pk,
        })

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(**self.get_answer_form_kwargs(self.question))
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Answer saved', extra_tags='show-icon')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.warning(
            self.request,
            'Answer not saved, please correct the form',
            extra_tags='show-icon',
        )
        return super().form_invalid(form)

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        try:
            return queryset.get(
                response=self.survey_response,
                question=self.question,
            )
        except self.model.DoesNotExist:
            # Perform create if object does not exist
            return None


class SurveyAnswerDocumentDelete(
    AjaxMixin,
    LoginRequiredMixin,
    DeleteView,
):
    model = SurveyAnswerDocument
    template_name = 'surveys/answer_document_delete.html'
    can_not_delete_msg = _(
        'You must have at least one document attached, please select '
        'in progress before you remove the document'
    )

    def get_success_url(self, *args, **kwargs):
        answer = self.object.answer
        if self.request.is_ajax():
            return reverse('survey-answer', kwargs={
                'pk': answer.response.pk,
                'question': answer.question.pk,
            })
        else:
            return reverse('survey-section', kwargs={
                'pk': answer.response.pk,
                'section': answer.question.section.pk,
            })

    def get_queryset(self):
        return super().get_queryset().filter(
            answer__response__organisation__pk=self.request.user.organisation_id,
        ).select_related(
            'document',
            'answer__response',
            'answer__question',
        )

    def get_context_data(self, **kwargs):
        kwargs.update(
            can_not_delete_msg=self.can_not_delete_msg,
            can_delete=self.can_delete(),
        )
        return super().get_context_data(**kwargs)

    def can_delete(self):
        answer = self.object.answer
        is_not_yes = answer.value != SurveyAnswer.ANSWER_YES
        other_documents = answer.documents.exclude(pk=self.object.pk)
        return is_not_yes or other_documents.exists()

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.can_delete():
            self.object.delete()
            messages.success(
                self.request,
                'Document successfully removed',
                extra_tags='show-icon',
            )
        else:
            messages.warning(
                self.request,
                self.can_not_delete_msg,
                extra_tags='show-icon',
            )

        success_url = self.get_success_url()
        return HttpResponseRedirect(success_url)


class SurveyAnswerDeleteView(
    AjaxMixin,
    LoginRequiredMixin,
    DeleteView,
):
    model = SurveyAnswer
    template_name = 'surveys/survey_answer_delete.html'

    def get_success_url(self, *args, **kwargs):
        answer = self.object
        if self.request.is_ajax():
            return reverse('survey-answer', kwargs={
                'pk': answer.response.pk,
                'question': answer.question.pk,
            })
        else:
            return reverse('survey-section', kwargs={
                'pk': answer.response.pk,
                'section': answer.question.section.pk,
            })

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        messages.success(
            self.request,
            'Answer successfully cleared',
            extra_tags='show-icon',
        )

        success_url = self.get_success_url()
        return HttpResponseRedirect(success_url)


class SurveyReportBase(
    LoginRequiredMixin,
    AssessmentMixin,
    SurveyViewMixin,
    UpdateView,
):
    model = SurveyResponse
    page_title = 'Assessment detail'
    form_class = SurveyLevelForm

    def get_survey_queryset(self, user):
        queryset = super().get_survey_queryset(user)
        return queryset.select_related('organisation')

    def get_object(self, queryset=None):
        return self.survey_response

    def get_page_title(self):
        return '%s - %s' % (self.object.organisation, self.survey.name)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            form_action=self.get_success_url(),
            report_name=self.report_name,
        )
        return context


class SurveyProgresssReport(SurveyReportBase):
    template_name = 'surveys/progress-report.html'
    report_name = 'Completion'

    def get_success_url(self):
        return reverse('survey-progress', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            progress=self.object.get_progress(),
        )
        return context


class SurveyComplianceReport(SurveyReportBase):
    template_name = 'surveys/compliance-report.html'
    report_name = 'Compliance'

    def get_success_url(self):
        return reverse('survey-compliance', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stats = self.object.get_compliance()
        compliance = stats['compliance']
        context.update(
            target_level_progress=compliance['levels'][self.object.level],
            progress=stats['progress'],
            compliance=compliance,
        )
        return context


class SurveyFullReport(SurveyReportBase):
    grantee_template_name = 'surveys/full-report.html'
    grantor_template_name = 'surveys/full-report-grantor.html'
    report_name = 'Full'

    def get_survey_queryset(self, user):
        """
        Return SurveyResponse objects available to grantee or grantor.

        The grantee user's organisation must match organisation.
        The  grantor user's organisation must be the grantor of an accepted invitation
        the same survey that has the survey_responses organisation as the grantee.
        """
        queryset = SurveyResponse.objects.filter(
            survey__questions__isnull=False,
        ).distinct()
        invitations = InvitationModel.objects.filter(
            survey=OuterRef('survey'),
            grantee=OuterRef('organisation'),
            accepted=True,
            grantor_id=user.organisation_id
        )
        queryset = queryset.annotate(
            invitation_id=Subquery(invitations.values('pk')[:1]),
        ).filter((
            Q(organisation__pk=user.organisation_id) |
            Q(
                submitted__isnull=False,
                invitation_id__isnull=False,
            )
        ))
        return queryset.select_related('organisation')

    def is_owner(self):
        return self.survey_response.organisation_id == self.request.user.organisation_id

    def get_template_names(self):
        template_name = self.grantee_template_name if self.is_owner() \
            else self.grantor_template_name
        return [template_name]

    def post(self, request, *args, **kwargs):
        """Restrict post to users from the survey_responses organisation"""

        if not self.is_owner():
            return self.http_method_not_allowed(request, *args, **kwargs)

        return super().post(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        organisation = self.request.user.organisation
        if not self.is_owner():
            if not organisation.active_subscription:
                message = (
                    "No active subscription. Your organization needs "
                    "an active subscription to view the report"
                )
                messages.warning(self.request, message, extra_tags='show-icon')
                if has_role(self.request.user, ['user', 'manager']):
                    return redirect(reverse('home'))
                return redirect(reverse('subscription'))

        return super().get(request, *args, **kwargs)

    def get_success_url(self, *args, **kwargs):
        return reverse('survey-report', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        stats = self.object.get_level_compliance()
        compliance = stats['compliance']

        stats_lookup = {step['section'].pk: step for step in compliance['sections']}

        questions = SurveyQuestion.objects.filter(
            survey=self.survey,
            level__lte=self.object.level,
        ).select_related(
            'section__area',
        ).prefetch_related(
            'options',
        )

        documents = SurveyAnswerDocument.objects.select_related('document')
        answers = SurveyAnswer.objects.filter(
            response=self.object,
            question__level__lte=self.object.level,
        ).prefetch_related(
            'options',
            Prefetch('documents', queryset=documents),
        )
        answers_lookup = answers.by_question()
        for question in questions:
            question.answer = answers_lookup.get(question.pk)
            step = stats_lookup.get(question.section.pk)
            try:
                step['questions'].append(question)
            except KeyError:
                step['questions'] = [question]

        context.update(
            questions=questions,
            progress=stats['progress'],
            compliance=compliance,
        )
        return context


class SubmitSurveyResponse(AjaxMixin, LoginRequiredMixin, SurveyViewMixin, UpdateView):
    form_class = SubmitForm
    template_name = 'surveys/submit.html'

    def get_survey_queryset(self, user):
        queryset = super().get_survey_queryset(user)
        return queryset.filter(submitted=None)

    def get_success_url(self, *args, **kwargs):
        return reverse('survey-report', kwargs={'pk': self.survey_response.pk})

    def get_object(self, queryset=None):
        return self.survey_response

    def form_valid(self, form):
        messages.success(
            self.request,
            'Assessment published successfully',
            extra_tags='show-icon',
        )
        # Update invitation status
        InvitationModel.objects.exclude(
            status=InvitationModel.INVITATION_SUBMITTED,
        ).filter(
            survey=self.object.survey,
            grantee=self.request.user.organisation,
        ).update(status=InvitationModel.INVITATION_SUBMITTED)

        return super().form_valid(form)


class InviteListView(
    LoginRequiredMixin,
    InvitesMixin,
    UserPassesTestMixin,
    PaginationMixin,
    ListView
):
    template_name = 'surveys/invites.html'
    page_title = 'Invitations'
    paginate_by = 10
    page_limit = 5
    context_object_name = "sent_invites"

    def test_func(self):
        return has_role(self.request.user, ['admin', 'manager'])

    def get_queryset(self):
        user = self.request.user
        qs = InvitationModel.objects.filter(
            grantor=user.organisation,
        ).with_submitted_response_id()
        return qs

    def _get_received_invites(self, user):
        qs = InvitationModel.objects.filter(grantee=user.organisation)
        return qs

    def get_context_data(self, **kwargs):
        user = self.request.user

        received_invites = self._get_received_invites(user)
        pending_invites_count = received_invites.filter(accepted=False).count()
        context = super().get_context_data(**kwargs)
        context.update(
            received_invites=received_invites,
            pending_invites_count=pending_invites_count,
        )

        return context


class CreateInviteView(LoginRequiredMixin, InvitesMixin, UserPassesTestMixin, CreateView):
    form_class = InvitationForm
    success_url = reverse_lazy('survey-invite')
    template_name = 'surveys/make_invitation.html'
    page_title = 'Make invitation'
    toggleValue = 'org'

    def test_func(self):
        return has_role(self.request.user, ['admin', 'manager'])

    def get(self, request, *args, **kwargs):
        self.object = None
        context = self.get_context_data(**kwargs)
        organisation = self.request.user.organisation
        if not organisation.active_subscription:
            message = (
                "No active subscription. Your organization needs "
                "an active subscription to make an invitations"
            )
            messages.warning(self.request, message, extra_tags='show-icon')
            if has_role(self.request.user, ['user', 'manager']):
                return redirect(reverse('home'))
            return redirect(reverse('subscription'))
        elif organisation.remaining_invites == 0:
            message = (
                "No invitations available. Your organization needs "
                "to purchase more invitations."
            )
            messages.warning(self.request, message, extra_tags='show-icon')
            if has_role(self.request.user, ['user', 'manager']):
                return redirect(reverse('home'))
            return redirect(reverse('subscription'))

        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'toggleValue': self.toggleValue
        })
        return context

    def form_valid(self, form):
        response = super().form_valid(form)

        if form.cleaned_data.get('is_organisation_invite'):
            self.object.send_invites()
        else:
            self.object.send_invites_unregistered()

        messages.success(self.request, (
            'Invitation sent successfully'
        ), extra_tags='show-icon')

        return response

    def form_invalid(self, form):
        self.object = None
        messages.warning(
            self.request, 'Invitation failed, please correct the form',
            extra_tags='show-icon'
        )
        is_organisation_invite = form.cleaned_data.get('is_organisation_invite')
        self.toggleValue = 'org' if is_organisation_invite else 'email'
        return self.render_to_response(self.get_context_data())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'grantor': self.request.user.organisation})
        return kwargs


class InviteAcceptView(AjaxMixin, LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'surveys/invite_accept_modal.html'

    def test_func(self):
        return has_role(self.request.user, ['admin', 'manager'])

    def _get_current_invite(self, **kwargs):
        pk = kwargs.pop('pk')
        return get_object_or_404(InvitationModel, id=pk)

    def _get_submitted(self, invitation):
        return invitation.survey.responses.filter(
            organisation=invitation.grantee,
            submitted__isnull=False,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invitation = self._get_current_invite(**kwargs)
        context = {
            'invitation': invitation,
            'level_name': get_level_name(invitation.level),
            'submitted': self._get_submitted(invitation).first(),
        }
        return context

    def post(self, request, *args, **kwargs):
        invitation = self._get_current_invite(**kwargs)
        invitation.accepted = True
        submitted = self._get_submitted(invitation).count()
        invitation.status = InvitationModel.INVITATION_SUBMITTED if submitted \
            else InvitationModel.INVITATION_PENDING
        invitation.save()
        messages.success(self.request, (
            'Successfully accepted the invitation'
        ), extra_tags='show-icon')

        return redirect(reverse('survey-invite'))


class ViewAssessmentList(
    LoginRequiredMixin,
    AssessmentMixin,
    UserPassesTestMixin,
    PaginationMixin,
    ListView,
):
    template_name = 'surveys/view_assessment.html'
    page_title = 'Assessments'
    paginate_by = 10
    page_limit = 5
    context_object_name = "shared_with_me"

    def test_func(self):
        return has_role(self.request.user, ['admin', 'manager', 'user'])

    def get_queryset(self):
        user = self.request.user
        qs = InvitationModel.objects.filter(
            grantor=user.organisation,
            accepted=True,
        ).with_submitted_response_id()
        return qs

    def _get_all_surveys(self, user):
        shared_with_others = InvitationModel.objects.filter(
            grantee=user.organisation,
            accepted=True
        )
        all_surveys = Survey.objects.filter(
            is_active=True,
        ).with_latest_response_progress(
            user.organisation,
            shared_with_others,
        )
        return all_surveys

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        surveys = self._get_all_surveys(user)
        context.update(
            surveys=surveys
        )

        return context


class ResendInviteView(LoginRequiredMixin, UserPassesTestMixin, View):

    def test_func(self):
        return has_role(self.request.user, ['admin', 'manager'])

    def _get_current_invite(self, **kwargs):
        pk = kwargs.pop('pk')
        return get_object_or_404(InvitationModel, id=pk)

    def post(self, request, *args, **kwargs):
        invitation = self._get_current_invite(**kwargs)
        invitation.send_invites()

        invitation.last_sent = timezone.now()
        invitation.save()

        messages.success(self.request, (
            'Your invite has been resent'
        ), extra_tags='show-icon')

        return redirect(reverse('survey-invite'))


class ExportSurveyQuestionView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):

    def test_func(self):
        return has_role(self.request.user, ['admin', 'manager', 'user'])

    def _get_survey_questions(self, survey):
        return SurveyQuestion.objects.filter(survey=survey)

    def _get_survey(self, **kwargs):
        pk = kwargs.pop('pk')
        return get_object_or_404(Survey, id=pk)

    def get(self, request, *args, **kwargs):

        survey = self._get_survey(**kwargs)

        response = HttpResponse(content_type='application/ms-excel')
        content_disposition = 'attachment; filename="{}.xls"'.format(survey.name)
        response['Content-Disposition'] = content_disposition

        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('Survey')

        row_num = 0
        sheet_style = xlwt.XFStyle()
        sheet_style.font.bold = True

        columns = [
            'Code',
            'Question',
            'Upload Required',
            'Notes',
            'Answer (yes/no)',
            'Explanation',
            'Due Date',
        ]

        for col_num, column in enumerate(columns):
            ws.write(row_num, col_num, column, sheet_style)

        sheet_style = xlwt.XFStyle()
        sheet_style.alignment.wrap = 1
        survey_questions = list(self._get_survey_questions(survey))

        for question in survey_questions:
            row_num += 1
            ws.write(row_num, 0, question.get_code(), sheet_style)
            ws.write(row_num, 1, strip_tags(question.name), sheet_style)
            ws.write(row_num, 2, question.get_upload_type_display(), sheet_style)
            ws.write(row_num, 3, strip_tags(question.notes or ''), sheet_style)

            for col_num in range(4, 7):
                ws.write(row_num, col_num, '', sheet_style)

        base_width = ws.col(1).width  # 2962
        ws.col(1).width = base_width * 3
        ws.col(3).width = base_width * 2
        ws.col(5).width = base_width * 3

        wb.save(response)
        return response
