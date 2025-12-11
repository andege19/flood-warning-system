"""
Django Admin configuration for Flood Warning System
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from core.models import (
    CustomUser, Ward, CrowdReport, WeatherDataLake, Alert, 
    FloodPrediction, SystemAlert, CrowdsourcedDataLake,
    HistoricalFloodEvent, FloodHistoricalData, SatelliteFloodData, 
    ClimatePatternData
)

# CustomUser Admin
class CustomUserAdmin(UserAdmin):
    """Admin interface for CustomUser"""
    
    model = CustomUser
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone_number')}),
        ('Role & Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'phone_number')
    ordering = ('-date_joined',)

# Ward Admin
class WardAdmin(admin.ModelAdmin):
    """Admin interface for Ward"""
    
    list_display = ('name', 'current_risk_level', 'population', 'last_updated')
    list_filter = ('current_risk_level', 'last_updated')
    search_fields = ('name',)
    readonly_fields = ('last_updated', 'geom_json')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'current_risk_level', 'population')
        }),
        ('Geographic Data', {
            'fields': ('geom_json',),
            'classes': ('collapse',)
        }),
        ('Infrastructure', {
            'fields': ('critical_infrastructure', 'safe_zones'),
            'classes': ('collapse',)
        }),
        ('System', {
            'fields': ('last_updated',),
            'classes': ('collapse',)
        }),
    )

# CrowdReport Admin
class CrowdReportAdmin(admin.ModelAdmin):
    """Admin interface for CrowdReport"""
    
    list_display = ('id', 'submitted_by', 'location_description', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'reliability_score')
    search_fields = ('submitted_by__username', 'location_description', 'report_text')
    readonly_fields = ('created_at', 'submitted_by')
    
    fieldsets = (
        ('Report Information', {
            'fields': ('submitted_by', 'status', 'created_at')
        }),
        ('Location', {
            'fields': ('ward', 'location_description', 'latitude', 'longitude')
        }),
        ('Report Content', {
            'fields': ('report_text', 'photos')
        }),
        ('Community Feedback', {
            'fields': ('reliability_score', 'upvotes', 'downvotes')
        }),
    )

# WeatherDataLake Admin
class WeatherDataLakeAdmin(admin.ModelAdmin):
    """Admin interface for WeatherDataLake"""
    
    list_display = ('ward', 'source', 'rainfall_mm', 'temperature_celsius', 'timestamp')
    list_filter = ('source', 'timestamp', 'ward')
    search_fields = ('ward__name',)
    readonly_fields = ('ingested_at', 'raw_data')
    
    fieldsets = (
        ('Data Source', {
            'fields': ('ward', 'source', 'timestamp', 'ingested_at')
        }),
        ('Weather Metrics', {
            'fields': ('rainfall_mm', 'temperature_celsius', 'humidity_percent', 'wind_speed_kmh', 'cloud_cover_percent')
        }),
        ('Satellite Data', {
            'fields': ('soil_moisture', 'vegetation_index'),
            'classes': ('collapse',)
        }),
        ('Raw Data', {
            'fields': ('raw_data',),
            'classes': ('collapse',)
        }),
    )

# FloodPrediction Admin
class FloodPredictionAdmin(admin.ModelAdmin):
    """Admin interface for FloodPrediction"""
    
    list_display = ('id', 'ward', 'predicted_risk_level', 'confidence_score', 'valid_from', 'created_at')
    list_filter = ('predicted_risk_level', 'valid_from', 'created_at')
    search_fields = ('ward__name',)
    readonly_fields = ('created_at', 'features_used')
    
    fieldsets = (
        ('Prediction', {
            'fields': ('ward', 'predicted_risk_level', 'confidence_score', 'created_at')
        }),
        ('Probabilities', {
            'fields': ('probability_low', 'probability_medium', 'probability_high')
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_until')
        }),
        ('Model Information', {
            'fields': ('model_version', 'features_used'),
            'classes': ('collapse',)
        }),
    )

# SystemAlert Admin
class SystemAlertAdmin(admin.ModelAdmin):
    """Admin interface for SystemAlert"""
    
    list_display = ('id', 'recipient', 'channel', 'status', 'created_at')
    list_filter = ('channel', 'status', 'created_at')
    search_fields = ('recipient__username', 'title', 'message')
    readonly_fields = ('created_at', 'sent_at', 'acknowledged_at')
    
    fieldsets = (
        ('Alert Information', {
            'fields': ('prediction', 'recipient', 'status', 'created_at')
        }),
        ('Content', {
            'fields': ('title', 'message', 'channel')
        }),
        ('Delivery', {
            'fields': ('sent_at', 'acknowledged_at', 'external_id'),
            'classes': ('collapse',)
        }),
    )

# Alert Admin (Legacy)
class AlertAdmin(admin.ModelAdmin):
    """Admin interface for Alert"""
    
    list_display = ('id', 'ward', 'risk_level', 'timestamp')
    list_filter = ('risk_level', 'timestamp')
    search_fields = ('ward__name', 'message_text')
    readonly_fields = ('timestamp',)

# CrowdsourcedDataLake Admin
class CrowdsourcedDataLakeAdmin(admin.ModelAdmin):
    """Admin interface for CrowdsourcedDataLake"""
    
    list_display = ('id', 'report', 'severity_score', 'affected_structures', 'created_at')
    list_filter = ('severity_score', 'created_at')
    search_fields = ('report__location_description',)
    readonly_fields = ('created_at',)

# HistoricalFloodEvent Admin
class HistoricalFloodEventAdmin(admin.ModelAdmin):
    """Admin for historical flood events"""
    
    list_display = ('event_name', 'date_occurred', 'risk_level', 'rainfall_mm', 'estimated_casualties')
    list_filter = ('risk_level', 'date_occurred', 'primary_cause')
    search_fields = ('event_name', 'description')
    filter_horizontal = ('affected_wards',)
    
    fieldsets = (
        ('Event Information', {
            'fields': ('event_name', 'description', 'date_occurred')
        }),
        ('Impact', {
            'fields': ('risk_level', 'estimated_casualties', 'estimated_displaced', 'estimated_damage_value')
        }),
        ('Environmental Data', {
            'fields': ('rainfall_mm', 'temperature_celsius', 'humidity_percent', 'wind_speed_kmh')
        }),
        ('Geographic', {
            'fields': ('affected_wards', 'latitude', 'longitude')
        }),
        ('Classification', {
            'fields': ('primary_cause', 'data_source', 'source_url')
        }),
    )

# ============================================
# FloodHistoricalData Admin
# ============================================
class FloodHistoricalDataAdmin(admin.ModelAdmin):
    """Admin for ward-year flood statistics"""
    
    list_display = ('ward', 'year', 'flood_count', 'flood_risk_score', 'vulnerability_index')
    list_filter = ('year', 'ward')
    search_fields = ('ward__name',)

# SatelliteFloodData Admin
class SatelliteFloodDataAdmin(admin.ModelAdmin):
    """Admin for satellite flood data"""
    
    list_display = ('historical_event', 'capture_date', 'satellite_source', 'inundated_area_sqkm')
    list_filter = ('satellite_source', 'capture_date', 'event_status')
    search_fields = ('historical_event__event_name',)

# ClimatePatternData Admin
class ClimatePatternDataAdmin(admin.ModelAdmin):
    """Admin for climate patterns"""
    
    list_display = ('ward', 'year', 'month', 'avg_rainfall_mm', 'flood_probability')
    list_filter = ('year', 'month', 'ward')

# Register Models
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Ward, WardAdmin)
admin.site.register(CrowdReport, CrowdReportAdmin)
admin.site.register(WeatherDataLake, WeatherDataLakeAdmin)
admin.site.register(FloodPrediction, FloodPredictionAdmin)
admin.site.register(SystemAlert, SystemAlertAdmin)
admin.site.register(Alert, AlertAdmin)
admin.site.register(CrowdsourcedDataLake, CrowdsourcedDataLakeAdmin)
admin.site.register(HistoricalFloodEvent, HistoricalFloodEventAdmin)
admin.site.register(FloodHistoricalData, FloodHistoricalDataAdmin)
admin.site.register(SatelliteFloodData, SatelliteFloodDataAdmin)
admin.site.register(ClimatePatternData, ClimatePatternDataAdmin)

# Customize Admin Site
admin.site.site_header = "Flood Warning System Administration"
admin.site.site_title = "Flood Warning Admin"
admin.site.index_title = "Welcome to Flood Warning System Administration"