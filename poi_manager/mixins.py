from django.db import models
from django.utils.translation import gettext_lazy as _

from .utils import CustomFieldJSONEncoder


__all__ = (
    'TimestampMixin',
    'CustomFieldsMixin',
    'CustomValidationMixin',
)


class TimestampMixin(models.Model):
    created = models.DateTimeField(
        verbose_name=_('created'),
        auto_now_add=True,
        blank=True,
        null=True
    )
    last_updated = models.DateTimeField(
        verbose_name=_('last updated'),
        auto_now=True,
        blank=True,
        null=True
    )

    class Meta:
        abstract = True


class CustomFieldsMixin(models.Model):
    custom_field_data = models.JSONField(
        encoder=CustomFieldJSONEncoder,
        blank=True,
        default=dict
    )

    class Meta:
        abstract = True


class CustomValidationMixin(models.Model):
    class Meta:
        abstract = True

    def clean(self):
        super().clean()
        # Custom validation logic can be added here if needed