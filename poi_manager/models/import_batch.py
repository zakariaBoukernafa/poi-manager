import uuid
from django.db import models
from django.utils import timezone

__all__ = ("ImportBatch",)


class ImportBatch(models.Model):
    """
    Tracks import operations for POI data files.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("partial", "Partially Completed"),
    ]

    FILE_TYPE_CHOICES = [
        ("csv", "CSV"),
        ("json", "JSON"),
        ("xml", "XML"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    file_path = models.CharField(max_length=500, verbose_name="File Path")

    file_name = models.CharField(max_length=255, verbose_name="File Name")

    file_type = models.CharField(
        max_length=10, choices=FILE_TYPE_CHOICES, verbose_name="File Type"
    )

    file_size = models.BigIntegerField(
        null=True, blank=True, verbose_name="File Size (bytes)"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True,
        verbose_name="Status",
    )

    started_at = models.DateTimeField(auto_now_add=True, verbose_name="Started At")

    completed_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Completed At"
    )

    records_processed = models.IntegerField(default=0, verbose_name="Records Processed")

    records_failed = models.IntegerField(default=0, verbose_name="Records Failed")

    records_skipped = models.IntegerField(
        default=0, verbose_name="Records Skipped (Duplicates)"
    )

    error_log = models.JSONField(default=dict, blank=True, verbose_name="Error Log")

    processing_time = models.DurationField(
        null=True, blank=True, verbose_name="Processing Time"
    )

    job_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="RQ Job ID",
        help_text="RQ Job ID for async processing",
    )

    class Meta:
        ordering = ["-started_at"]
        verbose_name = "Import Batch"
        verbose_name_plural = "Import Batches"

    def __str__(self):
        return f"{self.file_name} - {self.get_status_display()}"

    def mark_completed(self):
        """Mark the batch as completed and calculate processing time"""
        self.completed_at = timezone.now()
        self.processing_time = self.completed_at - self.started_at
        if self.records_failed > 0:
            self.status = "partial"
        else:
            self.status = "completed"
        self.save()

    def add_error(self, error_message, record_data=None):
        """Add an error to the error log"""
        if "errors" not in self.error_log:
            self.error_log["errors"] = []

        error_entry = {
            "timestamp": timezone.now().isoformat(),
            "message": str(error_message),
        }
        if record_data:
            error_entry["record"] = record_data

        self.error_log["errors"].append(error_entry)
        self.records_failed += 1
        self.save()
