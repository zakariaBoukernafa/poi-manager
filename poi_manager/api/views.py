from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import CursorPagination
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance
from django.contrib.postgres.search import TrigramSimilarity
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Prefetch
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.core.cache import cache

from poi_manager.models import PointOfInterest, ImportBatch
from poi_manager.filtersets import PointOfInterestFilterSet, ImportBatchFilterSet
from .serializers import PointOfInterestSerializer, ImportBatchSerializer

__all__ = (
    "PointOfInterestViewSet",
    "ImportBatchViewSet",
)


class FastPagination(CursorPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000
    ordering = "-created"


class PointOfInterestViewSet(viewsets.ModelViewSet):
    serializer_class = PointOfInterestSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = PointOfInterestFilterSet
    search_fields = ["name", "external_id", "description"]
    ordering_fields = ["name", "category", "avg_rating", "created"]
    ordering = ["name"]
    pagination_class = FastPagination

    def get_queryset(self):
        queryset = PointOfInterest.objects.select_related("import_batch")

        search = self.request.query_params.get("search")
        if search and len(search) >= 3:
            queryset = (
                queryset.annotate(similarity=TrigramSimilarity("name", search))
                .filter(similarity__gt=0.1)
                .order_by("-similarity")
            )

        return queryset

    @action(detail=False, methods=["get"])
    def nearby(self, request):
        try:
            lat = float(request.query_params.get("latitude"))
            lon = float(request.query_params.get("longitude"))
            radius = float(request.query_params.get("radius", 5))
            limit = int(request.query_params.get("limit", 20))

            cache_key = f"nearby_{lat:.4f}_{lon:.4f}_{radius}_{limit}"
            cached_result = cache.get(cache_key)
            if cached_result:
                return Response(cached_result)

            point = Point(lon, lat, srid=4326)
            nearby_pois = (
                PointOfInterest.objects.filter(
                    location__distance_lte=(point, Distance(km=radius))
                )
                .select_related("import_batch")
                .order_by("location")[:limit]
            )

            serializer = self.get_serializer(nearby_pois, many=True)
            cache.set(cache_key, serializer.data, 300)
            return Response(serializer.data)

        except (TypeError, ValueError):
            return Response(
                {"error": "Invalid parameters. Required: latitude, longitude (floats)"},
                status=400,
            )

    @action(detail=False, methods=["get"])
    @method_decorator(cache_page(60 * 15))
    def categories(self, request):
        cache_key = "poi_categories_with_counts"
        result = cache.get(cache_key)

        if not result:
            result = list(
                PointOfInterest.objects.values("category")
                .annotate(count=Count("id"))
                .order_by("category")
            )
            cache.set(cache_key, result, 900)

        return Response(result)


class ImportBatchViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ImportBatchSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ImportBatchFilterSet

    ordering_fields = ["started_at", "completed_at", "records_processed"]
    ordering = ["-started_at"]

    def get_queryset(self):
        return ImportBatch.objects.prefetch_related(
            Prefetch("pois", queryset=PointOfInterest.objects.only("id"))
        )

    @action(detail=False, methods=["get"])
    def recent(self, request):
        recent_batches = self.get_queryset()[:10]
        serializer = self.get_serializer(recent_batches, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    @method_decorator(cache_page(60 * 5))
    def statistics(self, request):
        cache_key = "import_batch_statistics"
        stats = cache.get(cache_key)

        if not stats:
            stats = {
                "total_imports": ImportBatch.objects.count(),
                "completed": ImportBatch.objects.filter(status="completed").count(),
                "failed": ImportBatch.objects.filter(status="failed").count(),
                "processing": ImportBatch.objects.filter(status="processing").count(),
                "total_pois_imported": PointOfInterest.objects.count(),
            }
            cache.set(cache_key, stats, 300)

        return Response(stats)
