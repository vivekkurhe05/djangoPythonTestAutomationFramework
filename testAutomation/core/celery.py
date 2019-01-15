from __future__ import absolute_import, unicode_literals

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks()

app.conf.CELERYBEAT_SCHEDULE = {
    'document_expiry': {
        'task': 'documents.tasks.check_document_expiry',
        'schedule': crontab(minute=0, hour='*/24'),
    },
}

app.conf.CELERY_TIMEZONE = 'UTC'


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
