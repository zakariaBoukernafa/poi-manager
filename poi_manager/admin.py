from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json

from poi_manager.models import PointOfInterest, ImportBatch


class PointOfInterestAdmin(admin.ModelAdmin):
    list_display = [
        "display_id",
        "name",
        "external_id",
        "category",
        "avg_rating_display",
        "rating_count",
        "source_file",
        "created",
    ]

    list_filter = ["category", "import_batch__file_type", "created", "import_batch"]

    search_fields = [
        "=id",
        "=external_id",
        "name",
        "category",
    ]

    readonly_fields = [
        "id",
        "created",
        "last_updated",
        "avg_rating",
        "rating_count",
        "location_display",
    ]

    fieldsets = (
        ("Identification", {"fields": ("id", "external_id", "name")}),
        ("Details", {"fields": ("category", "description")}),
        (
            "Location",
            {"fields": ("location", "latitude", "longitude", "location_display")},
        ),
        ("Ratings", {"fields": ("ratings", "avg_rating", "rating_count")}),
        (
            "Import Information",
            {"fields": ("source_file", "import_batch", "created", "last_updated")},
        ),
    )

    list_per_page = 50

    def display_id(self, obj):
        """Display internal ID with link."""
        url = reverse("admin:poi_manager_pointofinterest_change", args=[obj.id])
        return format_html('<a href="{}">{}</a>', url, obj.id)

    display_id.short_description = "Internal ID"
    display_id.admin_order_field = "id"

    def avg_rating_display(self, obj):
        """Display average rating with stars."""
        if obj.avg_rating:
            stars = "★" * int(obj.avg_rating) + "☆" * (5 - int(obj.avg_rating))
            return format_html(
                '{} <span style="color: gold;">{}</span>',
                round(obj.avg_rating, 2),
                stars,
            )
        return "-"

    avg_rating_display.short_description = "Avg Rating"
    avg_rating_display.admin_order_field = "avg_rating"

    def location_display(self, obj):
        """Display coordinates as formatted text."""
        if obj.location:
            return f"Lat: {obj.latitude:.6f}, Lon: {obj.longitude:.6f}"
        return "-"

    location_display.short_description = "Coordinates"

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related("import_batch")

    actions = ["recalculate_ratings", "export_to_csv"]

    def recalculate_ratings(self, request, queryset):
        """Recalculate average ratings for selected POIs."""
        updated = 0
        for poi in queryset:
            if poi.ratings:
                poi.avg_rating = sum(poi.ratings) / len(poi.ratings)
                poi.rating_count = len(poi.ratings)
                poi.save()
                updated += 1

        self.message_user(
            request, f"Successfully recalculated ratings for {updated} POIs."
        )

    recalculate_ratings.short_description = "Recalculate average ratings"

    def export_to_csv(self, request, queryset):
        """Export selected POIs to CSV."""
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="pois_export.csv"'

        writer = csv.writer(response)
        writer.writerow(
            [
                "Internal ID",
                "External ID",
                "Name",
                "Category",
                "Latitude",
                "Longitude",
                "Avg Rating",
                "Ratings Count",
            ]
        )

        for poi in queryset:
            writer.writerow(
                [
                    poi.id,
                    poi.external_id,
                    poi.name,
                    poi.category,
                    poi.latitude,
                    poi.longitude,
                    poi.avg_rating,
                    poi.rating_count,
                ]
            )

        return response

    export_to_csv.short_description = "Export to CSV"


class ImportBatchAdmin(admin.ModelAdmin):
    """
    Admin interface for Import Batches with progress monitoring.
    """

    list_display = [
        "batch_id_display",
        "file_name",
        "file_type",
        "status_display",
        "progress_display",
        "processing_time_display",
        "started_at",
        "actions_display",
    ]

    list_filter = ["status", "file_type", "started_at", "completed_at"]

    search_fields = ["id", "file_name", "file_path"]

    readonly_fields = [
        "id",
        "started_at",
        "completed_at",
        "processing_time",
        "job_id",
        "error_log_display",
        "statistics_display",
    ]

    fieldsets = (
        (
            "File Information",
            {"fields": ("file_path", "file_name", "file_type", "file_size")},
        ),
        (
            "Processing Status",
            {
                "fields": (
                    "status",
                    "started_at",
                    "completed_at",
                    "processing_time",
                    "job_id",
                )
            },
        ),
        (
            "Results",
            {
                "fields": (
                    "records_processed",
                    "records_failed",
                    "records_skipped",
                    "statistics_display",
                )
            },
        ),
        ("Errors", {"fields": ("error_log_display",), "classes": ("collapse",)}),
    )

    def batch_id_display(self, obj):
        """Display batch ID with link."""
        url = reverse("admin:poi_manager_importbatch_change", args=[obj.id])
        return format_html('<a href="{}">{}</a>', url, str(obj.id)[:8])

    batch_id_display.short_description = "Batch ID"

    def status_display(self, obj):
        """Display status with color coding."""
        colors = {
            "pending": "#FFA500",
            "processing": "#0080FF",
            "completed": "#00FF00",
            "failed": "#FF0000",
            "partial": "#FFFF00",
        }
        color = colors.get(obj.status, "#000000")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_display.short_description = "Status"
    status_display.admin_order_field = "status"

    def progress_display(self, obj):
        """Display import progress."""
        total = obj.records_processed + obj.records_failed + obj.records_skipped
        if total > 0:
            success_rate = (obj.records_processed / total) * 100
            return format_html(
                "{} / {} / {} <br>"
                '<div style="width:100px; background:#ddd;">'
                '<div style="width:{}%; background:#4CAF50; height:10px;"></div>'
                "</div>",
                obj.records_processed,
                obj.records_failed,
                obj.records_skipped,
                success_rate,
            )
        return "-"

    progress_display.short_description = "Processed / Failed / Skipped"

    def processing_time_display(self, obj):
        """Display processing time in human-readable format."""
        if obj.processing_time:
            total_seconds = int(obj.processing_time.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60

            if hours:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        return "-"

    processing_time_display.short_description = "Duration"

    def error_log_display(self, obj):
        """Display error log in formatted JSON."""
        if obj.error_log:
            formatted = json.dumps(obj.error_log, indent=2)
            return format_html(
                '<pre style="max-height: 300px; overflow-y: auto;">{}</pre>', formatted
            )
        return "No errors"

    error_log_display.short_description = "Error Log"

    def statistics_display(self, obj):
        """Display import statistics."""
        stats = []

        if obj.file_size:
            size_mb = obj.file_size / (1024 * 1024)
            stats.append(f"File Size: {size_mb:.2f} MB")

        if obj.processing_time and obj.records_processed > 0:
            seconds = obj.processing_time.total_seconds()
            rate = obj.records_processed / seconds if seconds > 0 else 0
            stats.append(f"Processing Rate: {rate:.0f} records/sec")

        success_rate = 0
        if obj.records_processed + obj.records_failed > 0:
            success_rate = (
                obj.records_processed / (obj.records_processed + obj.records_failed)
            ) * 100
            stats.append(f"Success Rate: {success_rate:.1f}%")

        return mark_safe("<br>".join(stats)) if stats else "-"

    statistics_display.short_description = "Statistics"

    def actions_display(self, obj):
        """Display action buttons."""
        buttons = []

        if obj.status == "completed":
            view_pois_url = (
                reverse("admin:poi_manager_pointofinterest_changelist")
                + f"?import_batch__id__exact={obj.id}"
            )
            buttons.append(f'<a class="button" href="{view_pois_url}">View POIs</a>')

        return mark_safe(" ".join(buttons)) if buttons else "-"

    actions_display.short_description = "Actions"

    actions = ["retry_failed_imports", "delete_with_pois"]

    def retry_failed_imports(self, request, queryset):
        """Retry failed import batches."""
        import django_rq
        from poi_manager.jobs import import_poi_file_async

        queue = django_rq.get_queue("default")
        retried = 0

        for batch in queryset.filter(status="failed"):
            queue.enqueue(import_poi_file_async, batch.id, batch.file_path, {})
            batch.status = "pending"
            batch.save()
            retried += 1

        self.message_user(request, f"Retrying {retried} failed import(s).")

    retry_failed_imports.short_description = "Retry failed imports"

    def delete_with_pois(self, request, queryset):
        """Delete import batches and associated POIs."""
        total_pois = 0
        for batch in queryset:
            total_pois += batch.pois.count()
            batch.delete()  # Cascades to POIs

        self.message_user(
            request, f"Deleted {queryset.count()} batch(es) and {total_pois} POIs."
        )

    delete_with_pois.short_description = "Delete batches with POIs"


admin.site.register(PointOfInterest, PointOfInterestAdmin)
admin.site.register(ImportBatch, ImportBatchAdmin)
