from datetime import date, timedelta

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.postgres.fields import CIEmailField
from django.contrib.sites.models import Site
from django.core import signing
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.functional import cached_property
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import ugettext_lazy as _

from incuna_mail import send
from orderable.models import Orderable

from rolepermissions.checkers import has_role
from rolepermissions.roles import get_user_roles

from user_management.models.mixins import VerifyEmailMixin

from surveys.models import get_level_name, LEVEL_CHOICES, Survey


def get_invitation_status(level):
    """Turn a status integer value into its display name."""
    return Invitation.INVITATION_STATUS_CHOICES[level - 1][1]


class OrganisationType(Orderable):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Organisation(models.Model):
    SIZE_CHOICES = (
        ('0-10', '0 - 10'),
        ('11-50', '11 - 50'),
        ('51-250', '51 - 250'),
        ('250+', '250+'),
    )
    EXPENDITURE_CHOICES = (
        ('0-20K', 'USD < 20K'),
        ('20K-100K', 'USD 20K - 100K'),
        ('100K-500K', 'USD 100K - 500K'),
        ('500K-5M', 'USD 500K - 5M'),
        ('5M-100M', 'USD 5M - 100M'),
        ('100M+', 'USD >100M'),
    )

    mobile_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Contact number must be entered in the format: '+919999999'.\
        Up to 15 digits allowed."
    )

    legal_name = models.CharField(
        verbose_name=_('Organization / Legal entity'),
        max_length=100,
        unique=True,
    )
    known_as = models.CharField(
        verbose_name=_('Organization name'),
        max_length=100,
        default='',
        blank=True,
    )
    acronym = models.CharField(max_length=100, default='', blank=True)
    parent_organisation = models.CharField(
        verbose_name=_('Parent / umbrella organization'),
        max_length=100,
        default='',
        blank=True,
    )

    registration_number = models.CharField(max_length=100, default='', blank=True)
    supporting_file = models.FileField(
        verbose_name=_('Registration supporting file'),
        upload_to='registration/supporting',
        max_length=255,
        default='',
        blank=True,
    )
    iati_uid = models.CharField(
        verbose_name=_('IATI UID'),
        max_length=100,
        default='',
        blank=True,
    )

    types = models.ManyToManyField(
        OrganisationType,
        verbose_name=_('Type of organization'),
        blank=False,
    )

    address_1 = models.CharField(max_length=255, default='')
    address_2 = models.CharField(max_length=255, default='', blank=True)
    city = models.CharField(verbose_name=_('City / Town'), max_length=100, default='')
    province = models.CharField(
        verbose_name=_('County/Province/District/State'),
        max_length=100,
        default='',
        blank=True,
    )
    zip = models.CharField(
        verbose_name=_('Postal code / ZIP'),
        max_length=100,
        default='',
        blank=True,
    )
    po_box = models.CharField(
        verbose_name=_('PO Box'),
        max_length=100,
        default='',
        blank=True,
    )
    country = models.ForeignKey(
        'countries.Country',
        on_delete=models.PROTECT,
        null=True,
        blank=False,
    )
    phone_number = models.CharField(
        validators=[mobile_regex],
        default='',
        max_length=20,
        blank=True,
    )
    landmark = models.CharField(max_length=100, default='', blank=True)

    size = models.CharField(
        verbose_name=_('Size'),
        max_length=30,
        choices=SIZE_CHOICES,
        default='',
        blank=True,
    )
    annual_expenditure = models.CharField(
        verbose_name=_('Annual Expenditure'),
        max_length=30,
        choices=EXPENDITURE_CHOICES,
        default='',
        blank=True,
    )
    website = models.URLField(max_length=100, default='', blank=True)
    social_media = models.URLField(
        verbose_name=_('Social Media'),
        max_length=100,
        default='',
        blank=True,
    )
    other_social_media = models.URLField(
        verbose_name=_('Other social media'),
        max_length=100,
        default='',
        blank=True,
    )
    biography = models.TextField(
        verbose_name=_('Biography'),
        default='',
        blank=True,
    )

    terms_acceptance_date = models.DateTimeField(default=timezone.now)
    privacy_acceptance_date = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('legal_name',)

    def __str__(self):
        return self.legal_name

    @cached_property
    def active_subscription(self):
        from subscriptions.models import Subscription
        return Subscription.objects.active_for_organisation(self)

    @cached_property
    def latest_subscription(self):
        from subscriptions.models import Subscription
        return Subscription.objects.latest_for_organisation(self)

    @cached_property
    def remaining_invites(self):
        return Invitation.objects.get_remaining_invites(self)


class User(PermissionsMixin, VerifyEmailMixin, AbstractBaseUser):
    # USER FIELDS
    '''A registered user model.'''

    mobile_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Contact number must be entered in the format: '+919999999'.\
        Up to 15 digits allowed."
    )

    user_mobile = models.CharField(
        validators=[mobile_regex], default='', max_length=20, blank=True
    )
    job_role = models.CharField(max_length=255, default='')
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)

    def send_welcome_invite(self, token_generator=default_token_generator):
        site = Site.objects.get_current()
        subject = 'Welcome to the Global Grant Community'
        user = self
        user_role = get_user_roles(user)[0].get_name()

        context = {
            'site': site,
            'email': user.email,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
            'site_domain': site.domain,
            'site_name': site.name,
            'organisation_name': self.organisation.legal_name,
            'user_name': user.name,
            'user_role': user_role.title()
        }

        send(
            to=user.email,
            subject=subject,
            template_name='organization/welcome_user.txt',
            context=context,
        )


class InvitationQueryset(models.QuerySet):

    def with_submitted_response_id(self):
        from surveys.models import SurveyResponse
        submitted_responses = SurveyResponse.objects.filter(
            survey=models.OuterRef('survey'),
            organisation=models.OuterRef('grantee'),
            submitted__isnull=False,
        ).order_by('-modified')
        return self.annotate(
            response_id=models.Subquery(submitted_responses.values('pk')[:1]),
        )

    def get_remaining_invites(self, organisation):
        from subscriptions.models import AssessmentPurchase, Order
        data = AssessmentPurchase.objects.filter(
            order__organisation=organisation,
            order__status=Order.STATUS_APPROVED
        ).unused().aggregate(
            total_included=models.Sum('number_included'),
            total_used=models.Sum('number_used'),
        )
        total_included = data.get('total_included', 0)
        total_used = data.get('total_used', 0)
        if not total_included:
            return 0
        if not total_used:
            return total_included
        return total_included - total_used


class Invitation(models.Model):
    from subscriptions.models import AssessmentPurchase
    INVITATION_AWAITING = 1
    INVITATION_PENDING = 2
    INVITATION_SUBMITTED = 3
    INVITATION_STATUS_CHOICES = (
        (INVITATION_AWAITING, 'Awaiting Acceptance'),
        (INVITATION_PENDING, 'Pending Submission'),
        (INVITATION_SUBMITTED, 'Submitted'),
    )

    grantor = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, related_name='grantor'
    )
    grantee = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, null=True, related_name='grantee'
    )
    grantee_email = CIEmailField(
        verbose_name=('Email address'),
        max_length=511,
        null=True
    )
    purchase = models.ForeignKey(
        AssessmentPurchase,
        related_name='invitations',
        null=True
    )
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    accepted = models.BooleanField(default=False)
    level = models.IntegerField(choices=LEVEL_CHOICES, default=1)
    status = models.IntegerField(choices=INVITATION_STATUS_CHOICES, default=1)
    created = models.DateTimeField(default=timezone.now)
    last_sent = models.DateTimeField(default=timezone.now)
    due_date = models.DateField(null=True, blank=True)

    objects = InvitationQueryset.as_manager()

    class Meta:
        ordering = ('-last_sent',)

    def __str__(self):
        return "{} {}".format(self.grantor, self.grantee)

    def highlight_due_date(self):
        if self.due_date:
            highlight_due_date = self.due_date - timedelta(days=2)
            if (self.status != 3) and (date.today() >= highlight_due_date):
                return True

        return False

    def send_invites(self, token_generator=default_token_generator):
        users = User.objects.filter(organisation=self.grantee)
        site = Site.objects.get_current()
        subject = 'Invitation to submit assessment'

        grantor_name = self.grantor.legal_name

        for user in users:
            if has_role(user, ['admin', 'manager']):
                context = {
                    'user_name': user.name,
                    'survey_level': get_level_name(self.level),
                    'survey_name': self.survey.name,
                    'grantor_name': grantor_name,
                    'email': user.email,
                    'site_domain': site.domain,
                    'survey_url': '',
                    'site_name': site.name,
                }
                send(
                    to=user.email,
                    subject=subject,
                    template_name='surveys/emails/invitation.txt',
                    context=context,
                )

    def send_invites_unregistered(self, token_generator=default_token_generator):
        site = Site.objects.get_current()
        subject = 'Invitation to submit assessment'
        invitation = self
        grantor_name = self.grantor.legal_name
        token = signing.dumps(invitation.id)

        context = {
            'site': site,
            'email': self.grantee_email,
            'user_email': invitation.grantee_email,
            'new_user': True,
            'token': token,
            'site_domain': site.domain,
            'site_name': site.name,
            'survey_level': get_level_name(self.level),
            'survey_name': self.survey.name,
            'grantor_name': grantor_name
        }

        send(
            to=invitation.grantee_email,
            subject=subject,
            template_name='surveys/emails/userinvite.txt',
            context=context,
        )
