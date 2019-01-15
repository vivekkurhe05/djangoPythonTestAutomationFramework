from __future__ import absolute_import, unicode_literals

from datetime import date, timedelta

from celery import shared_task

from dateutil.relativedelta import relativedelta

from django.contrib.sites.models import Site

from incuna_mail import send

from rolepermissions.checkers import has_role

from documents.models import Document
from users.models import User


def _send_notification(documents):
    site = Site.objects.get_current()
    subject = 'Action required - Document expiry notice.'
    for document in documents:
        users = User.objects.filter(organisation=document.organisation)
        for user in users:
            if has_role(user, ['admin', 'manager']):
                expires_in_days = relativedelta(document.expiry, date.today()).days
                if expires_in_days == 0:
                    expires_in_message = "today"
                else:
                    expires_in_message = "in {} days".format(expires_in_days)
                context = {
                    'site': site,
                    'site_domain': site.domain,
                    'site_name': site.name,
                    'email': user.email,
                    'document_expiry': document.expiry,
                    'document': document.name,
                    'organisation_name': user.organisation.legal_name,
                    'user_name': user.name,
                    'expires_in_message': expires_in_message,
                }
                send(
                    to=user.email,
                    subject=subject,
                    template_name='documents/document_expiry_email.txt',
                    context=context,
                )


def _to_be_expired(expiry_days=14):
    expiry_date = date.today() + timedelta(days=expiry_days)
    documents = Document.objects.filter(expiry=expiry_date)
    _send_notification(documents)


@shared_task
def check_document_expiry():
    _to_be_expired(expiry_days=14)
    _to_be_expired(expiry_days=0)
