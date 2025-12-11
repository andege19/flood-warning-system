from django.urls import path
from . import views

urlpatterns = [
    # ---  Authentication & Core Pages ---
    path("", views.home_view, name="home"),
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    
    # ---  Pages ---
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("map/", views.map_view, name="map"),
    path("report/", views.submit_report_page_view, name="submit-report-page"),
    
    # Authority dashboard - MUST be before API paths
    path("authority/dashboard/", views.authority_dashboard_view, name="authority-dashboard"),

    # --- API-like views for our application ---
    path("api/ward-data/", views.ward_data_view, name="ward-data"), 
    path("api/submit-report/", views.submit_report_view, name="submit-report"),

    # Report tracking
    path("report-status/<int:report_id>/", views.report_status_view, name="report-status"),

    # Authority email actions
    path('authority/report/<int:report_id>/reply/', views.send_report_reply_view, name='send-report-reply'),
    path('authority/send-ward-alert/', views.send_ward_alert_view, name='send-ward-alert'),
]