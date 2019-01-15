from collections import defaultdict

from django.db import models


class SurveyQueryset(models.QuerySet):
    def available(self):
        return self.filter(is_active=True, questions__isnull=False).distinct()

    def with_latest_response_progress(self, organisation, invitations=None):
        """
        Survey objects annotated with the organization's latest response with progress.
        If invitations are provided then they are annotated to the appropriate survey as
        a list of `survey.invitations`.

        Requires two additional queries to select response question and answer totals.
        """

        from .models import SurveyResponse

        all_responses = SurveyResponse.objects.filter(
            organisation=organisation,
            survey__in=self,
        ).order_by('modified')

        # We need two queries to annotate the answers total and questions total as
        # it is not possible to annotate them in the same query
        # https://code.djangoproject.com/ticket/10060
        with_questions = all_responses.with_questions_total()
        with_answers = all_responses.with_answers_total()

        # The responses are in ascending modified date order so if there are multiple
        # responses per survey the last (latest) response will be used.
        with_questions_lookup = {
            response.survey_id: response
            for response in with_questions
        }
        with_answers_lookup = {
            response.survey_id: response
            for response in with_answers
        }

        if invitations is None:
            invitations = []
        invite_lookup = defaultdict(list)
        for invite in invitations:
            invite_lookup[invite.survey_id].append(invite)

        for survey in self:
            try:
                response = with_questions_lookup[survey.pk]
            except KeyError:
                survey.survey_response = None
            else:
                response.answers_total = with_answers_lookup[survey.pk].answers_total
                response.progress = response.get_progress_info(
                    response.answers_total,
                    response.questions_total,
                )
                response.summary_url = response.get_summary_url(
                    response.progress['is_complete'],
                )
                survey.survey_response = response

            survey.invites = invite_lookup[survey.id]

            yield survey


class SurveyQuestionQueryset(models.QuerySet):
    def for_survey(self, survey):
        return self.filter(survey=survey)

    def for_level(self, survey, level):
        """Return every question that must be answered for this level."""
        return self.filter(survey=survey, level__lte=level)

    def for_section(self, survey, section):
        return self.filter(survey=survey, section=section)

    def next_section(self, survey, current_section=None):
        """
        Return the section after this one, or the first section if current_section
        isn't specified.
        """
        qs = self.filter(survey=survey)
        if current_section:
            qs = qs.filter(
                models.Q(
                    section__area__number=current_section.area.number,
                    section__number__gt=current_section.number,
                ) | models.Q(
                    section__area__number__gt=current_section.area.number,
                )
            )
        first = qs.order_by('section').first()
        return first.section_id if first else None

    def previous_section(self, survey, current_section):
        """Return the section before this one"""
        qs = self.filter(survey=survey)
        qs = qs.filter(
            models.Q(
                section__area__number=current_section.area.number,
                section__number__lt=current_section.number,
            ) | models.Q(
                section__area__number__lt=current_section.area.number,
            )
        )
        first = qs.order_by('-section').first()
        return first.section_id if first else None


class SurveyResponseQueryset(models.QuerySet):
    def for_user(self, user):
        queryset = self.filter(survey__questions__isnull=False).distinct()
        return queryset.filter(organisation__pk=user.organisation_id)

    def with_answers_total(self):
        return self.annotate(
            answers_total=models.Sum(models.Case(
                models.When(answers__question__level__lte=models.F('level'), then=1),
                output_field=models.IntegerField(),
                default=0,
            )),
        )

    def with_questions_total(self):
        return self.annotate(
            questions_total=models.Sum(models.Case(
                models.When(survey__questions__level__lte=models.F('level'), then=1),
                output_field=models.IntegerField(),
                default=0,
            )),
        )


class SurveyAnswerQueryset(models.QuerySet):
    def by_question(self):
        """Return the answers as a dictionary keyed by question_id"""

        return {answer.question_id: answer for answer in self}

    def results(self):
        """
        Return the aggregated results.
            {
                'total': 27,
                'yes': 20,
                'no': 7,
                'in-progress': 0,
                'not-applicable': 0,
            }
        """
        # Generate a aggregated sum for each choice value
        kwargs = {
            value: models.Sum(models.Case(
                models.When(value=value, then=1),
                output_field=models.IntegerField(),
                default=0,
            ))
            for value, _label in self.model.ANSWER_CHOICES
        }
        return self.aggregate(
            total=models.Count('id'),
            **kwargs,
        )
