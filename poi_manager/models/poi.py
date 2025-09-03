from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from poi_manager.mixins import TimestampMixin, CustomFieldsMixin, CustomValidationMixin

__all__ = ("PointOfInterest",)


class PointOfInterest(
    TimestampMixin, CustomFieldsMixin, CustomValidationMixin, models.Model
):
    id = models.BigAutoField(primary_key=True, verbose_name="Internal ID")
    external_id = models.CharField(
        max_length=255,
        db_index=True,
        unique=True,
        verbose_name="External ID",
        help_text="Original ID from the source file",
    )

    name = models.CharField(
        max_length=500,
        verbose_name="POI Name",
        db_index=True,
        help_text="Name of the point of interest",
    )

    category = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name="Category",
        help_text="Category of the POI (e.g., restaurant, beach, bus-stop)",
    )

    location = models.PointField(
        geography=True,
        spatial_index=True,
        verbose_name="Location",
        help_text="Geographic coordinates of the POI",
    )

    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        verbose_name="Latitude",
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )

    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        verbose_name="Longitude",
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )

    ratings = ArrayField(
        models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(5)]),
        default=list,
        blank=True,
        verbose_name="Ratings",
        help_text="Array of individual ratings",
    )

    avg_rating = models.FloatField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Average Rating",
        help_text="Calculated average of all ratings",
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )

    rating_count = models.IntegerField(
        default=0, verbose_name="Rating Count", help_text="Number of ratings"
    )

    description = models.TextField(
        blank=True,
        verbose_name="Description",
        help_text="Additional description from JSON files",
    )

    source_file = models.CharField(
        max_length=255,
        verbose_name="Source File",
        help_text="Name of the file this POI was imported from",
    )

    import_batch = models.ForeignKey(
        "ImportBatch",
        on_delete=models.CASCADE,
        related_name="pois",
        verbose_name="Import Batch",
    )

    class Meta:
        ordering = ["name", "category"]
        verbose_name = "Point of Interest"
        verbose_name_plural = "Points of Interest"
        indexes = [
            models.Index(fields=["category", "avg_rating"]),
            models.Index(fields=["external_id"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.category})"

    def save(self, *args, **kwargs):
        if self.ratings:
            self.avg_rating = sum(self.ratings) / len(self.ratings)
            self.rating_count = len(self.ratings)
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.latitude and self.longitude:
            from django.contrib.gis.geos import Point

            self.location = Point(float(self.longitude), float(self.latitude))


@receiver([post_save, post_delete], sender=PointOfInterest)
def invalidate_poi_cache(sender, instance, **kwargs):
    from django.core.cache import cache

    cache.delete("poi_categories_with_counts")
    cache.delete("import_batch_statistics")
