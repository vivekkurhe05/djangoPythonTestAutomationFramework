from django.db import models
from django.utils import timezone

from users.models import Organisation


class Document(models.Model):
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    file = models.FileField(max_length=255, null=True)
    expiry = models.DateField(null=True, blank=True)
    created = models.DateTimeField(default=timezone.now, editable=False)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
