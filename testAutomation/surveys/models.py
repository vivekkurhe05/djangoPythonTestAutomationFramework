from functools import partial

from django.contrib.postgres.fields import JSONField
from django.core.validators import MinValueValidator, ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from orderable.models import Orderable

from surveys.querysets import (
    SurveyAnswerQueryset,
    SurveyQueryset,
    SurveyQuestionQueryset,
    SurveyResponseQueryset,
)

LEVEL_CHOICES = (
    (1, 'Bronze'),
    (2, 'Silver'),
    (3, 'Gold'),
    (4, 'Platinum'),
)


def get_level_name(level):
    """Turn a level's integer value into its display name."""
    return LEVEL_CHOICES[level - 1][1]


class Survey(models.Model):
    name = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)

    objects = SurveyQueryset.as_manager()

    def __str__(self):
        return self.name

    def get_sections(self):
        """Return a list of sections available for this survey."""
        sections = SurveySection.objects.filter(
            surveyquestion__survey=self,
        )
        sections = sections.select_related('area')
        sections = sections.distinct()
        return sections


class SurveyArea(models.Model):
    name = models.CharField(max_length=255)
    number = models.IntegerField(unique=True)

    class Meta:
        ordering = ['number']

    def __str__(self):
        return self.name


class SurveySection(models.Model):
    area = models.ForeignKey(SurveyArea, related_name='survey_area')
    name = models.CharField(max_length=255)
    number = models.IntegerField(validators=[MinValueValidator(1)])

    class Meta:
        ordering = ['area', 'number']

    def __str__(self):
        return self.name

    def get_code(self):
        return '{}.{}'.format(self.area.number, self.number)


class SurveyQuestion(models.Model):
    UPLOAD_TYPES = (
        ('policy', _('Policy')),
        ('procedure', _('Procedure')),
        ('process', _('Process')),
    )
    survey = models.ForeignKey(Survey, related_name='questions')
    section = models.ForeignKey(
        SurveySection, on_delete=models.PROTECT, default=None
    )

    name = models.TextField()
    notes = models.TextField(blank=True)
    level = models.IntegerField(choices=LEVEL_CHOICES)
    question_number = models.IntegerField(validators=[MinValueValidator(1)])

    upload_type = models.CharField(max_length=255, blank=True, choices=UPLOAD_TYPES)
    reference = models.URLField(max_length=255, blank=True)

    objects = SurveyQuestionQueryset.as_manager()

    class Meta:
        ordering = ('section', 'level', 'question_number')

    def get_code(self):
        """Return the full 4-digit code."""
        return '{}.{}.{}'.format(
            self.section.get_code(),
            self.level,
            self.question_number,
        )
    get_code.short_description = _('code')
    get_code.admin_order_field = 'section'

    def __str__(self):
        return self.name


class SurveyQuestionOption(Orderable):
    name = models.CharField(max_length=255)
    question = models.ForeignKey(SurveyQuestion, related_name='options')

    def __str__(self):
        return self.name

    class Meta(Orderable.Meta):
        unique_together = (('question', 'name'),)


class SurveyResponse(models.Model):
    PROGRESS_LABELS = {
        'no-question': _('No questions for this tier'),
        'not-started': _('Not yet started'),
        'in-progress': _('In progress'),
        'complete': _('Complete'),
    }
    organisation = models.ForeignKey('users.Organisation', related_name='responses')
    survey = models.ForeignKey(Survey, related_name='responses')
    created = models.DateTimeField(default=timezone.now, editable=False)
    modified = models.DateTimeField(auto_now=True)
    submitted = models.DateTimeField(editable=False, null=True)
    answers_old = JSONField(default={})
    level = models.IntegerField(
        verbose_name=_('target tier'),
        choices=LEVEL_CHOICES,
        blank=True,
    )

    objects = SurveyResponseQueryset.as_manager()

    class Meta:
        ordering = ('created',)

    def get_summary_url(self, is_complete=False):
        if is_complete:
            return reverse('survey-compliance', kwargs={'pk': self.pk})
        else:
            return reverse('survey-progress', kwargs={'pk': self.pk})

    @classmethod
    def get_progress_info(cls, count, total):
        count = min(count, total)
        is_complete = False
        if total == 0:
            slug = 'no-question'
            is_complete = True
        elif count == 0:
            slug = 'not-started'
        elif count < total:
            slug = 'in-progress'
        else:
            slug = 'complete'
            is_complete = True
        try:
            ratio = count / total
        except ZeroDivisionError:
            ratio = 0
        return {
            'total': total,
            'count': count,
            'slug': slug,
            'label': cls.PROGRESS_LABELS[slug],
            'ratio': ratio,
            'percentage': round(ratio * 100),
            'is_complete': is_complete,
        }

    @classmethod
    def _build_level_stats(cls, answered, questions, key_formater):
        levels = {}
        for level, label in LEVEL_CHOICES:
            key = key_formater(level)
            questions_count = questions[key] or 0
            answered_count = answered[key] or 0
            info = cls.get_progress_info(answered_count, questions_count)
            info.update({
                'level': level,
                'label': label,
            })
            levels[level] = info
        return levels

    @classmethod
    def _count_when(cls, then=1, **kwargs):
        """Utility method to generate ORM/SQL to count rows based on filter conditions"""
        return models.Sum(models.Case(
            models.When(then=then, **kwargs),
            output_field=models.IntegerField(),
            default=0,
        ))

    def get_section_question_counts(self, sections):
        """
        Aggregate the count of questions per section in a single query by selecting
        the sum of the questions for each section.
        """
        return self.survey.questions.filter(level__lte=self.level).aggregate(
            total=models.Count('id'),
            **{
                str(section.pk): self._count_when(section=section)
                for section in sections
            }
        )

    def get_progress(self):
        """
        Return the overall progress and per section by aggregating questions and answers.

        Uses 3 queries and returns of the form:
        {
            'sections': [
                {
                    'section': section,
                    'total': 1,
                    'count': 1,
                    'slug': 'complete',
                    'label': 'Complete',
                    'ratio': 1.0,
                    'percentage': 100,
                },
                {
                    'section': section,
                    'total': 3,
                    'count': 2,
                    'slug': 'in-progress',
                    'label': 'In progress',
                    'ratio': 2 / 3,
                    'percentage': 67,
                },
                {
                    'section': section,
                    'total': 1,
                    'count': 0,
                    'slug': 'not-started',
                    'label': 'Not yet started',
                    'ratio': 0.0,
                    'percentage': 0,
                },
            ],
            'total': 5,
            'compliance_total': 1,
            'count': 3,
            'ratio': 3 / 5,
            'percentage': 60,
            'slug': 'in-progress',
            'label': 'In progress',
        }

        """
        sections = self.survey.get_sections()

        questions = self.get_section_question_counts(sections)

        # Aggregate the count of answers per section in a single query by selecting
        # the sum of the answers for each section.
        answered = self.answers.filter(question__level__lte=self.level).aggregate(
            total=models.Count('id'),
            compliance_total=self._count_when(value=SurveyAnswer.ANSWER_YES),
            **{
                str(section.pk): self._count_when(question__section=section)
                for section in sections
            }
        )

        steps = []
        for section in sections:
            questions_count = questions[str(section.pk)] or 0
            answered_count = answered[str(section.pk)] or 0
            info = self.get_progress_info(answered_count, questions_count)
            info.update({'section': section})
            steps.append(info)

        questions_count = questions['total'] or 0
        answered_count = answered['total'] or 0
        compliance_count = answered['compliance_total'] or 0
        info = self.get_progress_info(answered_count, questions_count)
        info.update({
            'sections': steps,
            'compliance': self.get_progress_info(compliance_count, questions_count),
        })
        return info

    def get_compliance(self):
        """
        Return the overall progress and per level and per section compliance by
        aggregating questions and correct (yes) answers.

        Uses 3 queries and returns of the form:
        {
            'progress': {
                'total': 5,
                'count': 3,
                'ratio': 3 / 5,
                'percentage': 60,
                'slug': 'in-progress',
                'label': 'In progress',
            },
            'compliance': {
                'levels': {
                    1: {
                        'slug': 'complete',
                        'label': 'Bronze',
                        'level': 1,
                        'count': 1,
                        'total': 1,
                        'percentage': 100,
                        'ratio': 1.0,
                    },
                    2: {
                        'slug': 'in-progress',
                        'label': 'Silver',
                        'level': 2,
                        'count': 1,
                        'total': 5,
                        'percentage': 20,
                        'ratio': 1 / 5,
                    },
                    3: {
                        'slug': 'in-progress',
                        'label': 'Gold',
                        'level': 3,
                        'count': 2,
                        'total': 6,
                        'percentage': 33,
                        'ratio': 2 / 6,
                    },
                    4: {
                        'slug': 'in-progress',
                        'label': 'Platinum',
                        'level': 4,
                        'count': 2,
                        'total': 6,
                        'percentage': 33,
                        'ratio': 2 / 6,
                    },
                },
                'sections': [
                    {
                        'levels': [
                            {
                                'count': 1,
                                'label': 'Bronze',
                                'level': 1,
                                'percentage': 100,
                                'total': 1,
                                'ratio': 1.0,
                                'slug': 'complete',
                            },
                            {
                                'count': 1,
                                'label': 'Silver',
                                'level': 2,
                                'percentage': 100,
                                'total': 1,
                                'ratio': 1.0,
                                'slug': 'complete',
                            },
                            {
                                'count': 1,
                                'label': 'Gold',
                                'level': 3,
                                'percentage': 100,
                                'total': 1,
                                'ratio': 1.0,
                                'slug': 'complete',
                            },
                            {
                                'count': 1,
                                'label': 'Platinum',
                                'level': 4,
                                'percentage': 100,
                                'total': 1,
                                'ratio': 1.0,
                                'slug': 'complete',
                            },
                        ],
                        'section': section,
                    },
                    {
                        'levels': [
                            {
                                'count': 0,
                                'label': 'Bronze',
                                'level': 1,
                                'percentage': 0,
                                'total': 0,
                                'ratio': 0,
                                'slug': 'not-started',
                            },
                            {
                                'count': 0,
                                'label': 'Silver',
                                'level': 2,
                                'percentage': 0,
                                'total': 3,
                                'ratio': 0.0,
                                'slug': 'not-started',
                            },
                            {
                                'count': 0,
                                'label': 'Gold',
                                'level': 3,
                                'percentage': 0,
                                'total': 3,
                                'ratio': 0.0,
                                'slug': 'not-started',
                            },
                            {
                                'count': 0,
                                'label': 'Platinum',
                                'level': 4,
                                'percentage': 0,
                                'total': 3,
                                'ratio': 0.0,
                                'slug': 'not-started',
                            },
                        ],
                        'section': section,
                    },
                    {
                        'levels': [
                            {
                                'count': 0,
                                'label': 'Bronze',
                                'level': 1,
                                'percentage': 0,
                                'total': 0,
                                'ratio': 0,
                                'slug': 'not-started',
                            },
                            {
                                'count': 0,
                                'label': 'Silver',
                                'level': 2,
                                'percentage': 0,
                                'total': 1,
                                'ratio': 0.0,
                                'slug': 'not-started',
                            },
                            {
                                'count': 1,
                                'label': 'Gold',
                                'level': 3,
                                'percentage': 50,
                                'total': 2,
                                'ratio': 1 / 2,
                                'slug': 'in-progress',
                            },
                            {
                                'count': 1,
                                'label': 'Platinum',
                                'level': 4,
                                'percentage': 50,
                                'total': 2,
                                'ratio': 1 / 2,
                                'slug': 'in-progress',
                            },
                        ],
                        'section': section,
                    },
                ],
            }
        }
        """
        sections = self.survey.get_sections()

        # Build kwargs to aggregate questions and answers counts.
        question_kwargs = {}
        answer_kwargs = {}
        for level, _label in LEVEL_CHOICES:
            level_key = str(level)
            question_kwargs[level_key] = self._count_when(level__lte=level)
            answer_kwargs[level_key] = self._count_when(
                question__level__lte=level,
                value=SurveyAnswer.ANSWER_YES,
            )
            for section in sections:
                key = '{}-{}'.format(level, section.pk)
                question_kwargs[key] = self._count_when(section=section, level__lte=level)
                answer_kwargs[key] = self._count_when(
                    question__section=section,
                    question__level__lte=level,
                    value=SurveyAnswer.ANSWER_YES,
                )

        questions = self.survey.questions.aggregate(
            total=self._count_when(level__lte=self.level),
            **question_kwargs
        )
        answered = self.answers.aggregate(
            total=self._count_when(question__level__lte=self.level),
            **answer_kwargs
        )

        steps = []
        for section in sections:
            keyformater = partial('{}-{section}'.format, section=section.pk)
            levels = list(self._build_level_stats(
                answered,
                questions,
                keyformater,
            ).values())

            steps.append({
                'section': section,
                'levels': levels,
            })

        levels = self._build_level_stats(answered, questions, str)

        questions_count = questions['total'] or 0
        answered_count = answered['total'] or 0
        progress = self.get_progress_info(answered_count, questions_count)

        return {
            'progress': progress,
            'compliance': {
                'levels': levels,
                'sections': steps,
            },
        }

    def get_level_compliance(self):
        """
        Return the overall progress and per section compliance for the current level
        by aggregating questions and correct (yes) answers.

        Uses 3 queries and returns of the form:
        {
            'compliance': {
                'count': 1,
                'label': 'In progress',
                'percentage': 20,
                'ratio': 0.2,
                'sections': [
                    {
                        'count': 1,
                        'label': 'Complete',
                        'percentage': 100,
                        'ratio': 1.0,
                        'section': section,
                        'slug': 'complete',
                        'total': 1,
                    },
                    {
                        'count': 0,
                        'label': 'Not yet started',
                        'percentage': 0,
                        'ratio': 0.0,
                        'section': section,
                        'slug': 'not-started',
                        'total': 3,
                    },
                    {
                        'count': 0,
                        'label': 'Not yet started',
                        'percentage': 0,
                        'ratio': 0.0,
                        'section': section,
                        'slug': 'not-started',
                        'total': 1,
                    }
                ],
                'slug': 'in-progress',
                'total': 5,
            },
            'progress': {
                'count': 3,
                'label': 'In progress',
                'percentage': 60,
                'ratio': 0.6,
                'slug': 'in-progress',
                'total': 5,
            }
        }
        """
        sections = self.survey.get_sections()
        questions = self.get_section_question_counts(sections)
        answered = self.answers.filter(question__level__lte=self.level).aggregate(
            total=models.Count('id'),
            compliance_total=self._count_when(value=SurveyAnswer.ANSWER_YES),
            **{
                str(section.pk): self._count_when(
                    question__section=section,
                    value=SurveyAnswer.ANSWER_YES,
                )
                for section in sections
            }
        )

        steps = []
        for section in sections:
            questions_count = questions[str(section.pk)] or 0
            answered_count = answered[str(section.pk)] or 0
            info = self.get_progress_info(answered_count, questions_count)
            info.update({'section': section})
            steps.append(info)

        questions_count = questions['total'] or 0
        answered_count = answered['total'] or 0
        progress = self.get_progress_info(answered_count, questions_count)

        compliance_count = answered['compliance_total'] or 0
        compliance = self.get_progress_info(compliance_count, questions_count)
        compliance['sections'] = steps

        return {
            'progress': progress,
            'compliance': compliance,
        }


class SurveyAnswer(models.Model):
    ANSWER_YES = 'yes'
    ANSWER_PROGRESS = 'in-progress'
    ANSWER_NO = 'no'
    ANSWER_NA = 'not-applicable'

    ANSWER_CHOICES = (
        (ANSWER_YES, _('Yes')),
        (ANSWER_PROGRESS, _('In progress')),
        (ANSWER_NO, _('No')),
        (ANSWER_NA, _('Not Applicable')),
    )
    response = models.ForeignKey(SurveyResponse, related_name='answers')
    question = models.ForeignKey(SurveyQuestion, related_name='answers')
    value = models.CharField(max_length=233, choices=ANSWER_CHOICES)
    explanation = models.TextField(blank=True)
    due_date = models.DateField(blank=True, null=True)
    options = models.ManyToManyField(
        SurveyQuestionOption,
        related_name='answers',
        blank=True,
    )

    objects = SurveyAnswerQueryset.as_manager()

    class Meta:
        unique_together = (('response', 'question'),)

    def __str__(self):
        return self.get_value_display()


class SurveyAnswerDocument(models.Model):
    answer = models.ForeignKey(
        SurveyAnswer,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    document = models.ForeignKey(
        'documents.Document',
        on_delete=models.PROTECT,
        related_name='questions'
    )
    explanation = models.TextField(blank=True)
    created = models.DateTimeField(default=timezone.now, editable=False)

    def __str__(self):
        return '{} - {} - {}'.format(
            self.created.strftime('%Y-%m-%d %H:%M:%S'),
            self.answer_id,
            self.document_id,
        )

    def clean(self):
        if self.document.organisation != self.answer.response.organisation:
            raise ValidationError(
                _('The {document} and {answer} {organisation} must match').format(
                    document=self.document._meta.verbose_name,
                    answer=self.answer._meta.verbose_name,
                    organisation=self.document.organisation._meta.verbose_name_plural,
                )
            )
