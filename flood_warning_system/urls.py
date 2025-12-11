from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core import views

urlpatterns = [
    # Admin panel
    path("admin/", admin.site.urls),
    
    # Core app URLs
    path("", views.home_view, name="home"),
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("map/", views.map_view, name="map"),
    path("submit-report/", views.submit_report_page_view, name="submit-report-page"),
    path("submit-report-api/", views.submit_report_view, name="submit-report"),
    path("report/<int:report_id>/", views.report_status_view, name="report-status"),
    path("authority/dashboard/", views.authority_dashboard_view, name="authority-dashboard"),
    path("authority/report/<int:report_id>/validate/", views.validate_report_view, name="validate-report"),
    path("authority/report/<int:report_id>/reject/", views.reject_report_view, name="reject-report"),
    
    # Flood Information Routes
    path("flood-information/", views.flood_information_view, name="flood-information"),
    path("historical-event/<int:event_id>/", views.historical_event_detail_view, name="historical-event-detail"),
    path("ward/<int:ward_id>/flood-history/", views.ward_flood_history_view, name="ward-flood-history"),
    
    # API endpoints
    path("api/ward-data/", views.ward_data_view, name="ward-data"),
    path("api/historical-flood-data/", views.historical_flood_data_api, name="historical-flood-data"),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])