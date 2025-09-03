from rest_framework.routers import DefaultRouter
from . import views

# Create router and register viewsets
router = DefaultRouter()
router.register("pois", views.PointOfInterestViewSet, basename="poi")
router.register("import-batches", views.ImportBatchViewSet, basename="importbatch")

# URL patterns
urlpatterns = router.urls
