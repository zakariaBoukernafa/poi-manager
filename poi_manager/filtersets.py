import django_filters
from django_filters import FilterSet
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance
from .models import PointOfInterest, ImportBatch

__all__ = (
    "PointOfInterestFilterSet",
    "ImportBatchFilterSet",
)


class PointOfInterestFilterSet(FilterSet):
    id = django_filters.NumberFilter(field_name="id", lookup_expr="exact")
    external_id = django_filters.CharFilter(
        field_name="external_id", lookup_expr="exact"
    )

    category = django_filters.CharFilter(field_name="category", lookup_expr="iexact")
    category_contains = django_filters.CharFilter(
        field_name="category", lookup_expr="icontains"
    )

    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")

    min_rating = django_filters.NumberFilter(field_name="avg_rating", lookup_expr="gte")
    max_rating = django_filters.NumberFilter(field_name="avg_rating", lookup_expr="lte")

    min_latitude = django_filters.NumberFilter(field_name="latitude", lookup_expr="gte")
    max_latitude = django_filters.NumberFilter(field_name="latitude", lookup_expr="lte")
    min_longitude = django_filters.NumberFilter(
        field_name="longitude", lookup_expr="gte"
    )
    max_longitude = django_filters.NumberFilter(
        field_name="longitude", lookup_expr="lte"
    )

    def filter_nearby(self, queryset, name, value):
        if not value:
            return queryset

        try:
            parts = value.split(",")
            if len(parts) != 3:
                return queryset

            lat = float(parts[0])
            lon = float(parts[1])
            radius = float(parts[2])

            point = Point(lon, lat, srid=4326)
            return queryset.filter(location__distance_lte=(point, Distance(km=radius)))
        except (ValueError, IndexError):
            return queryset

    nearby = django_filters.CharFilter(method="filter_nearby")

    class Meta:
        model = PointOfInterest
        fields = [
            "id",
            "external_id",
            "name",
            "category",
            "latitude",
            "longitude",
            "avg_rating",
            "source_file",
            "import_batch",
        ]


class ImportBatchFilterSet(FilterSet):
    status = django_filters.ChoiceFilter(choices=ImportBatch.STATUS_CHOICES)
    file_type = django_filters.ChoiceFilter(choices=ImportBatch.FILE_TYPE_CHOICES)

    started_after = django_filters.DateTimeFilter(
        field_name="started_at", lookup_expr="gte"
    )
    started_before = django_filters.DateTimeFilter(
        field_name="started_at", lookup_expr="lte"
    )
    completed_after = django_filters.DateTimeFilter(
        field_name="completed_at", lookup_expr="gte"
    )
    completed_before = django_filters.DateTimeFilter(
        field_name="completed_at", lookup_expr="lte"
    )

    class Meta:
        model = ImportBatch
        fields = [
            "id",
            "file_name",
            "file_type",
            "status",
            "started_at",
            "completed_at",
        ]
