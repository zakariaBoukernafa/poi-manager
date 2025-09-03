from rest_framework import serializers
from poi_manager.models import PointOfInterest, ImportBatch

__all__ = (
    "PointOfInterestSerializer",
    "ImportBatchSerializer",
)


class PointOfInterestSerializer(serializers.ModelSerializer):
    location = serializers.CharField(read_only=True)

    class Meta:
        model = PointOfInterest
        fields = [
            "id",
            "external_id",
            "name",
            "category",
            "latitude",
            "longitude",
            "location",
            "ratings",
            "avg_rating",
            "rating_count",
            "description",
            "source_file",
            "import_batch",
            "created",
            "last_updated",
        ]
        read_only_fields = ["avg_rating", "rating_count", "created", "last_updated"]


class ImportBatchSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    file_type_display = serializers.CharField(
        source="get_file_type_display", read_only=True
    )
    poi_count = serializers.IntegerField(source="pois.count", read_only=True)

    class Meta:
        model = ImportBatch
        fields = [
            "id",
            "file_path",
            "file_name",
            "file_type",
            "file_type_display",
            "file_size",
            "status",
            "status_display",
            "started_at",
            "completed_at",
            "processing_time",
            "records_processed",
            "records_failed",
            "records_skipped",
            "error_log",
            "poi_count",
        ]
        read_only_fields = [
            "id",
            "file_path",
            "file_name",
            "file_type",
            "file_size",
            "status",
            "started_at",
            "completed_at",
            "records_processed",
            "records_failed",
            "records_skipped",
            "error_log",
        ]
