from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

from django.core.urlresolvers import reverse_lazy
from django.views.generic import CreateView, UpdateView

from core.mixins import AppMixin

from .forms import AddDocumentForm, EditDocumentForm
from .models import Document


class DocumentMixin(LoginRequiredMixin, AppMixin):
    sidebar_item = 'document'
    page_title = 'Document library'


class DocumentHome(DocumentMixin, CreateView):
    template_name = 'document.html'
    form_class = AddDocumentForm
    success_url = reverse_lazy('document-home')

    def _get_document_list(self, user):
        qs = Document.objects.filter(organisation=user.organisation)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        document_list = self._get_document_list(self.request.user)
        context.update({
            'document_list': document_list
        })

        return context

    def form_valid(self, form):
        form.instance.organisation = self.request.user.organisation

        messages.success(
            self.request,
            'Document uploaded successfully',
            extra_tags='show-icon',
        )

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.warning(
            self.request,
            'Failed to upload document',
            extra_tags='show-icon',
        )

        return super().form_invalid(form)


class DocumentEdit(DocumentMixin, UpdateView):
    template_name = 'document_edit.html'
    form_class = EditDocumentForm
    success_url = reverse_lazy('document-home')
    model = Document

    def form_valid(self, form):
        messages.success(self.request, (
            'Document updated successfully'
        ), extra_tags='show-icon')

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.warning(self.request, (
            'Failed to update document'
        ), extra_tags='show-icon')

        return super().form_invalid(form)
