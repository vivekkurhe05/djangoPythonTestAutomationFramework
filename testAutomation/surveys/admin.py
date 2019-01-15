from django.contrib import admin
from django.db import models
from orderable.admin import OrderableTabularInline
from tinymce.widgets import AdminTinyMCE

from .models import (
    Survey,
    SurveyAnswer,
    SurveyArea,
    SurveyQuestion,
    SurveyQuestionOption,
    SurveyResponse,
    SurveySection,
)


class SurveyAdmin(admin.ModelAdmin):
    save_as = True
    list_display = (
        'name',
        'is_active',
    )
    list_filter = ('name', 'is_active',)

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        self.original_object_id = object_id
        return super(SurveyAdmin, self).changeform_view(
            request,
            object_id,
            form_url,
            extra_context,
        )

    def save_model(self, request, obj, form, change):
        super(SurveyAdmin, self).save_model(request, obj, form, change)
        if '_saveasnew' in request.POST:
            questions = SurveyQuestion.objects.filter(survey__pk=self.original_object_id)
            to_add = []
            for question in questions:
                question.id = None
                question.survey = obj
                to_add.append(question)
            SurveyQuestion.objects.bulk_create(to_add)


class SurveyQuestionOptionInline(OrderableTabularInline):
    model = SurveyQuestionOption


class SurveyQuestionAdmin(admin.ModelAdmin):
    list_display = (
        'survey',
        'get_code',
        'area',
        'section',
        'level',
        'question_number',
        'name',
    )
    list_filter = ('survey', 'section__area', 'section', 'level',)
    formfield_overrides = {
        models.TextField: {'widget': AdminTinyMCE},
    }
    inlines = (SurveyQuestionOptionInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'section__area',
        )

    def area(self, obj):
        return obj.section.area
    area.admin_order_field = 'section__area'


class SurveyAreaAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'number',
    )
    list_filter = ('name', 'number',)


class SurveySectionAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'number',
        'area',
    )
    list_editable = ('area',)
    list_filter = ('area', 'name', 'number',)


class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = (
        'organisation',
        'survey',
        'level',
        'created',
        'modified',
        'submitted',
    )
    list_filter = ('organisation', 'survey', 'level',)
    readonly_fields = ('created', 'modified', 'submitted')
    fields = ('organisation', 'survey', 'level') + readonly_fields


class SurveyAnswerAdmin(admin.ModelAdmin):
    list_display = ('survey', 'organisation', 'question', 'value')
    list_display_links = ('survey', 'organisation', 'question')
    list_filter = ('response__survey', 'response__organisation', 'question', 'value')

    raw_id_fields = ['response', 'question']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'response__survey',
            'response__organisation',
        )

    def survey(self, obj):
        return obj.response.survey
    survey.admin_order_field = 'response__survey'

    def organisation(self, obj):
        return obj.response.organisation
    organisation.admin_order_field = 'response__organisation'


admin.site.register(Survey, SurveyAdmin)
admin.site.register(SurveyQuestion, SurveyQuestionAdmin)
admin.site.register(SurveyResponse, SurveyResponseAdmin)
admin.site.register(SurveyAnswer, SurveyAnswerAdmin)
admin.site.register(SurveyArea, SurveyAreaAdmin)
admin.site.register(SurveySection, SurveySectionAdmin)
