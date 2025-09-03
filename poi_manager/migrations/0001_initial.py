# Generated migration for POI Manager models

from django.contrib.gis.db import models as gis_models
from django.contrib.postgres.fields import ArrayField
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion
import poi_manager.utils


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ImportBatch",
            fields=[
                (
                    "id",
                    models.UUIDField(primary_key=True, serialize=False, editable=False),
                ),
                (
                    "file_path",
                    models.CharField(max_length=500, verbose_name="File Path"),
                ),
                (
                    "file_name",
                    models.CharField(max_length=255, verbose_name="File Name"),
                ),
                (
                    "file_type",
                    models.CharField(
                        choices=[("csv", "CSV"), ("json", "JSON"), ("xml", "XML")],
                        max_length=10,
                        verbose_name="File Type",
                    ),
                ),
                ("file_size", models.BigIntegerField(verbose_name="File Size (bytes)")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("processing", "Processing"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                        ],
                        default="pending",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                (
                    "started_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Started At"),
                ),
                (
                    "completed_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Completed At"
                    ),
                ),
                (
                    "records_processed",
                    models.IntegerField(default=0, verbose_name="Records Processed"),
                ),
                (
                    "records_failed",
                    models.IntegerField(default=0, verbose_name="Records Failed"),
                ),
                (
                    "records_skipped",
                    models.IntegerField(default=0, verbose_name="Records Skipped"),
                ),
                (
                    "error_log",
                    models.JSONField(
                        blank=True,
                        default=list,
                        encoder=poi_manager.utils.CustomFieldJSONEncoder,
                        verbose_name="Error Log",
                    ),
                ),
                (
                    "job_id",
                    models.CharField(
                        blank=True, max_length=255, null=True, verbose_name="RQ Job ID"
                    ),
                ),
            ],
            options={
                "verbose_name": "Import Batch",
                "verbose_name_plural": "Import Batches",
                "ordering": ["-started_at"],
            },
        ),
        migrations.CreateModel(
            name="PointOfInterest",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        primary_key=True, serialize=False, verbose_name="Internal ID"
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "custom_field_data",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        encoder=poi_manager.utils.CustomFieldJSONEncoder,
                    ),
                ),
                (
                    "external_id",
                    models.CharField(
                        db_index=True,
                        max_length=255,
                        unique=True,
                        verbose_name="External ID",
                        help_text="Original ID from the source file",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        db_index=True,
                        max_length=500,
                        verbose_name="POI Name",
                        help_text="Name of the point of interest",
                    ),
                ),
                (
                    "category",
                    models.CharField(
                        db_index=True,
                        max_length=100,
                        verbose_name="Category",
                        help_text="Category of the POI (e.g., restaurant, beach, bus-stop)",
                    ),
                ),
                (
                    "location",
                    gis_models.PointField(
                        geography=True,
                        spatial_index=True,
                        srid=4326,
                        verbose_name="Location",
                        help_text="Geographic coordinates of the POI",
                    ),
                ),
                (
                    "latitude",
                    models.DecimalField(
                        decimal_places=7,
                        max_digits=10,
                        verbose_name="Latitude",
                        validators=[
                            django.core.validators.MinValueValidator(-90),
                            django.core.validators.MaxValueValidator(90),
                        ],
                    ),
                ),
                (
                    "longitude",
                    models.DecimalField(
                        decimal_places=7,
                        max_digits=10,
                        verbose_name="Longitude",
                        validators=[
                            django.core.validators.MinValueValidator(-180),
                            django.core.validators.MaxValueValidator(180),
                        ],
                    ),
                ),
                (
                    "ratings",
                    ArrayField(
                        base_field=models.FloatField(
                            validators=[
                                django.core.validators.MinValueValidator(0),
                                django.core.validators.MaxValueValidator(5),
                            ]
                        ),
                        blank=True,
                        default=list,
                        size=None,
                        verbose_name="Ratings",
                        help_text="Array of individual ratings",
                    ),
                ),
                (
                    "avg_rating",
                    models.FloatField(
                        blank=True,
                        db_index=True,
                        null=True,
                        verbose_name="Average Rating",
                        help_text="Calculated average of all ratings",
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(5),
                        ],
                    ),
                ),
                (
                    "rating_count",
                    models.IntegerField(
                        default=0,
                        verbose_name="Rating Count",
                        help_text="Number of ratings",
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True,
                        verbose_name="Description",
                        help_text="Additional description from JSON files",
                    ),
                ),
                (
                    "source_file",
                    models.CharField(
                        max_length=255,
                        verbose_name="Source File",
                        help_text="Name of the file this POI was imported from",
                    ),
                ),
                (
                    "import_batch",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pois",
                        to="poi_manager.importbatch",
                        verbose_name="Import Batch",
                    ),
                ),
            ],
            options={
                "verbose_name": "Point of Interest",
                "verbose_name_plural": "Points of Interest",
                "ordering": ["name", "category"],
            },
        ),
        migrations.AddIndex(
            model_name="pointofinterest",
            index=models.Index(
                fields=["category", "avg_rating"], name="poi_manager_categor_f8e9c0_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="pointofinterest",
            index=models.Index(
                fields=["external_id"], name="poi_manager_externa_c63dcf_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="pointofinterest",
            index=models.Index(fields=["name"], name="poi_manager_name_b8c9a5_idx"),
        ),
    ]
