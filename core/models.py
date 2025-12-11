from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
from django.conf import settings

# --- Ward Model ---
class Ward(models.Model):
    RISK_CHOICES = (
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    )
    
    name = models.CharField(max_length=100)
    
    # We will store the ward's map boundaries as GeoJSON text.
    geom_json = models.TextField(help_text="GeoJSON coordinates for the ward boundary", default="")
    
    current_risk_level = models.CharField(max_length=10, choices=RISK_CHOICES, default='Low')
    last_updated = models.DateTimeField(auto_now=True)

    # Add new fields for enhanced data
    population = models.IntegerField(default=0)
    critical_infrastructure = models.JSONField(default=dict,
        help_text="Hospitals, schools, etc.")
    safe_zones = models.JSONField(default=dict,
        help_text="Evacuation points")
    
    class Meta:
        indexes = [
            models.Index(fields=['current_risk_level']),
        ]

    def __str__(self):
        return self.name

# --- CustomUser Model ---
class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('resident', 'Resident'),
        ('authority', 'Authority'),
    )
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='resident')
    phone_number = models.CharField(max_length=20, blank=True, null=True, help_text="Used for SMS alerts")

    subscribed_wards = models.ManyToManyField(
        Ward, 
        blank=True, 
        related_name="subscribers"
    )

    def __str__(self):
        return self.username

# --- CrowdReport Model ---
class CrowdReport(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Validated', 'Validated'),
        ('Rejected', 'Rejected'),
    )

    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    ward = models.ForeignKey(Ward, on_delete=models.SET_NULL, null=True, blank=True)
    
    # We add a default value to prevent the prompt.
    report_text = models.TextField(
        help_text="Detailed description of the flood report.", 
        default="No report text provided."
    )
    
    location_description = models.CharField(
        max_length=255, 
        help_text="e.g., 'Corner of Main St.'",
        default="No location description provided"
    )
    
    latitude = models.FloatField(null=True, blank=True) 
    longitude = models.FloatField(null=True, blank=True)
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    # Add photo support
    photos = models.ImageField(
        upload_to='flood_reports/%Y/%m/%d/',
        null=True,
        blank=True,
        help_text='Upload a photo of the flood situation'
    )
    
    # Add crowdsourcing features
    reliability_score = models.FloatField(default=0.5,
                                         help_text="0-1 score based on user history")
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)

    def __str__(self):
        return f"Report from {self.submitted_by.username} ({self.status})"

# --- Alert Model ---
class Alert(models.Model):
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name="alerts")
    risk_level = models.CharField(max_length=10, choices=Ward.RISK_CHOICES)
    message_text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.risk_level} Alert for {self.ward.name} at {self.timestamp}"

# --- WeatherData Model ---
class WeatherData(models.Model):
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name="weather_data")
    rainfall_mm = models.FloatField()
    river_level_m = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Data for {self.ward.name} at {self.timestamp}"

# WeatherDataLake Model 
class WeatherDataLake(models.Model):
    """
    Stores raw weather data from multiple sources
    for historical analysis and ML training
    """
    SOURCE_CHOICES = (
        ('KMD', 'Kenya Meteorological Department'),
        ('GPM', 'Global Precipitation Measurement'),
        ('CHIRPS', 'Climate Hazards Group'),
        ('OPEN_METEO', 'Open-Meteo API'),
    )
    
    ward = models.ForeignKey('Ward', on_delete=models.CASCADE, related_name='weather_data_lake')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    
    # JSONB for flexible data storage
    raw_data = models.JSONField(help_text="Raw weather data from source")
    
    # Extracted metrics
    rainfall_mm = models.FloatField(null=True, blank=True)
    temperature_celsius = models.FloatField(null=True, blank=True)
    humidity_percent = models.FloatField(null=True, blank=True)
    wind_speed_kmh = models.FloatField(null=True, blank=True)
    cloud_cover_percent = models.FloatField(null=True, blank=True)
    
    # Satellite-specific fields
    soil_moisture = models.FloatField(null=True, blank=True)
    vegetation_index = models.FloatField(null=True, blank=True)
    
    timestamp = models.DateTimeField(db_index=True)
    ingested_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['ward', 'timestamp']),
            models.Index(fields=['source', 'timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.source} - {self.ward.name} ({self.timestamp})"

# CrowdsourcedDataLake Model
class CrowdsourcedDataLake(models.Model):
    """
    Enhanced crowdsourced data storage with photo support
    """
    report = models.OneToOneField('CrowdReport', on_delete=models.CASCADE, 
                                  related_name='data_lake_entry')
    
    # Photo URLs (stored in cloud storage)
    photo_urls = ArrayField(models.URLField(), blank=True, null=True)
    
    # Extracted data from photos (using computer vision)
    water_level_estimated = models.FloatField(null=True, blank=True)
    affected_area_sqm = models.FloatField(null=True, blank=True)
    
    # Severity indicators
    severity_score = models.IntegerField(choices=[(i, i) for i in range(1, 11)],
                                        help_text="1-10 severity scale")
    
    # Structured data for ML
    affected_structures = models.IntegerField(default=0)
    people_affected = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Crowdsourced Data - {self.report.id}"

# FloodPrediction Model
class FloodPrediction(models.Model):
    """
    Stores ML model predictions for audit trail
    """
    ward = models.ForeignKey('Ward', on_delete=models.CASCADE, 
                           related_name='predictions')
    
    # Prediction details
    predicted_risk_level = models.CharField(max_length=10, 
                                           choices=Ward.RISK_CHOICES)
    confidence_score = models.FloatField(help_text="0-1 confidence")
    
    # Probability for each class
    probability_low = models.FloatField()
    probability_medium = models.FloatField()
    probability_high = models.FloatField()
    
    # Features used in prediction
    features_used = models.JSONField()
    model_version = models.CharField(max_length=20)
    
    # Prediction window
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['ward', 'valid_from']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.ward.name} - {self.predicted_risk_level} ({self.confidence_score})"

# === NEW: Alert Model (Enhanced) ===
class SystemAlert(models.Model):
    """
    Enhanced alert system for multi-channel notifications
    """
    CHANNEL_CHOICES = (
        ('SMS', 'SMS via Twilio'),
        ('WHATSAPP', 'WhatsApp'),
        ('EMAIL', 'Email'),
        ('IN_APP', 'In-App Notification'),
        ('WEB_PUSH', 'Web Push'),
    )
    
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
        ('ACKNOWLEDGED', 'Acknowledged'),
    )
    
    # Alert trigger
    prediction = models.ForeignKey('FloodPrediction', on_delete=models.CASCADE,
                                  related_name='alerts')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, 
                                 on_delete=models.CASCADE)
    
    # Alert details
    title = models.CharField(max_length=200)
    message = models.TextField()
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, 
                            default='PENDING')
    sent_at = models.DateTimeField(null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    external_id = models.CharField(max_length=200, null=True, blank=True,
                                  help_text="ID from external service")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['recipient', 'status']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.channel} Alert to {self.recipient.username}"

# --- Historical Flood Data Models ---
class HistoricalFloodEvent(models.Model):
    """Historical flood occurrences in Nairobi (2015-2025)"""
    
    RISK_LEVELS = [
        ('Low', 'Low Risk'),
        ('Medium', 'Medium Risk'),
        ('High', 'High Risk'),
    ]
    
    # Event information
    event_name = models.CharField(max_length=255)
    description = models.TextField()
    date_occurred = models.DateField()
    
    # Geographic information
    affected_wards = models.ManyToManyField(Ward, related_name='historical_floods')
    latitude = models.FloatField()
    longitude = models.FloatField()
    
    # Impact assessment
    risk_level = models.CharField(max_length=20, choices=RISK_LEVELS)
    estimated_casualties = models.IntegerField(default=0)
    estimated_displaced = models.IntegerField(default=0)
    estimated_damage_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Environmental data
    rainfall_mm = models.FloatField(help_text="Rainfall recorded during event")
    temperature_celsius = models.FloatField(null=True, blank=True)
    humidity_percent = models.IntegerField(null=True, blank=True)
    wind_speed_kmh = models.FloatField(null=True, blank=True)
    
    # Classification
    primary_cause = models.CharField(
        max_length=100,
        choices=[
            ('heavy_rainfall', 'Heavy Rainfall'),
            ('poor_drainage', 'Poor Drainage'),
            ('river_overflow', 'River Overflow'),
            ('dam_failure', 'Dam Failure'),
            ('poor_infrastructure', 'Poor Infrastructure'),
            ('climate_change', 'Climate Change'),
        ]
    )
    
    # Sources
    data_source = models.CharField(max_length=255, help_text="Source of data (e.g., NDMA, news, reports)")
    source_url = models.URLField(null=True, blank=True)
    
    # System fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_occurred']
        verbose_name = 'Historical Flood Event'
        verbose_name_plural = 'Historical Flood Events'
        indexes = [
            models.Index(fields=['-date_occurred']),
            models.Index(fields=['risk_level']),
        ]
    
    def __str__(self):
        return f"{self.event_name} ({self.date_occurred.year})"


class FloodHistoricalData(models.Model):
    """Aggregated historical flood data by ward and year"""
    
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name='historical_data')
    year = models.IntegerField()
    
    # Flood frequency
    flood_count = models.IntegerField(default=0)
    avg_rainfall_mm = models.FloatField(default=0)
    max_rainfall_mm = models.FloatField(default=0)
    
    # Impact metrics
    total_affected = models.IntegerField(default=0)
    total_displaced = models.IntegerField(default=0)
    total_casualties = models.IntegerField(default=0)
    
    # Risk assessment
    flood_risk_score = models.FloatField(help_text="0-100 risk score")
    vulnerability_index = models.FloatField(help_text="0-100 vulnerability score")
    
    # Satellite data (if available)
    inundation_area_sqkm = models.FloatField(null=True, blank=True)
    vegetation_loss_percent = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('ward', 'year')
        ordering = ['-year']
    
    def __str__(self):
        return f"{self.ward.name} - {self.year} (Risk: {self.flood_risk_score})"


class SatelliteFloodData(models.Model):
    """Satellite-derived flood extent data"""
    
    EVENT_STATUS = [
        ('pre_flood', 'Pre-Flood'),
        ('during_flood', 'During Flood'),
        ('post_flood', 'Post-Flood'),
    ]
    
    historical_event = models.ForeignKey(
        HistoricalFloodEvent,
        on_delete=models.CASCADE,
        related_name='satellite_data'
    )
    
    # Satellite information
    satellite_source = models.CharField(
        max_length=100,
        choices=[
            ('sentinel_1', 'Sentinel-1 SAR'),
            ('sentinel_2', 'Sentinel-2 Optical'),
            ('landsat_8', 'Landsat 8'),
            ('modis', 'MODIS'),
        ]
    )
    
    capture_date = models.DateField()
    event_status = models.CharField(max_length=20, choices=EVENT_STATUS)
    
    # Flood metrics
    inundated_area_sqkm = models.FloatField()
    water_depth_estimate_m = models.FloatField(null=True, blank=True)
    confidence_percent = models.IntegerField(help_text="Data confidence 0-100%")
    
    # Data
    raw_data_url = models.URLField(help_text="Link to raw satellite data")
    processed_geojson = models.JSONField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-capture_date']
    
    def __str__(self):
        return f"{self.get_satellite_source_display()} - {self.capture_date}"


class ClimatePatternData(models.Model):
    """Long-term climate patterns for ML training"""
    
    MONTH_CHOICES = [(i, f"Month {i}") for i in range(1, 13)]
    
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name='climate_patterns')
    month = models.IntegerField(choices=MONTH_CHOICES)
    year = models.IntegerField()
    
    # Climate metrics
    avg_rainfall_mm = models.FloatField()
    avg_temperature_celsius = models.FloatField()
    avg_humidity_percent = models.IntegerField()
    
    # Historical flood correlation
    has_flood_occurred = models.BooleanField(default=False)
    flood_probability = models.FloatField(default=0.0, help_text="0-1 probability")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('ward', 'month', 'year')
        ordering = ['-year', 'month']
    
    def __str__(self):
        return f"{self.ward.name} - {self.month}/{self.year}"
    
    def get_month_display(self):
        months = {
            1: 'January', 2: 'February', 3: 'March', 4: 'April',
            5: 'May', 6: 'June', 7: 'July', 8: 'August',
            9: 'September', 10: 'October', 11: 'November', 12: 'December'
        }
        return months.get(self.month, f'Month {self.month}')

# Email Log Model
class EmailLog(models.Model):
    """Log all emails sent by the system"""
    RECIPIENT_TYPES = [
        ('user', 'User'),
        ('authority', 'Authority'),
    ]
    
    recipient_email = models.EmailField()
    recipient_type = models.CharField(max_length=20, choices=RECIPIENT_TYPES)
    subject = models.CharField(max_length=255)
    email_type = models.CharField(max_length=50)  # report_confirmation, report_validated, etc.
    related_report = models.ForeignKey(CrowdReport, null=True, blank=True, on_delete=models.CASCADE)
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('sent', 'Sent'), ('failed', 'Failed')], default='sent')
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-sent_at']
        verbose_name_plural = "Email Logs"
    
    def __str__(self):
        return f"{self.email_type} to {self.recipient_email} - {self.sent_at.strftime('%Y-%m-%d %H:%M')}"

# ReportAction Model 
class ReportAction(models.Model):
    """Store admin actions and notes on reports"""
    ACTION_CHOICES = [
        ('validated', 'Validated'),
        ('rejected', 'Rejected'),
    ]
    
    report = models.ForeignKey(CrowdReport, on_delete=models.CASCADE, related_name='actions')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True, help_text="Admin notes sent to user")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_action_display()} - Report #{self.report.id} by {self.admin.username}"