from django.urls import path, include
from django.views.generic import TemplateView

app_name = "poi_manager"

urlpatterns = [
    # API URLs
    path("api/", include("poi_manager.api.urls")),
    # Web interface URLs (placeholder for now)
    # These would be implemented if we add web views later
    path("", TemplateView.as_view(template_name="admin/base.html"), name="poi_list"),
]
