"""
Celery configuration for Flood Warning System
"""

import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flood_warning_system.settings')

app = Celery('flood_warning_system')

# Load configuration from Django settings, namespace='CELERY'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    'ingest-weather-data': {
        'task': 'core.tasks.ingest_weather_data',
        'schedule': crontab(minute=0, hour='*/2'),  # Every 2 hours
    },
    'predict-flood-risk': {
        'task': 'core.tasks.predict_flood_risk',
        'schedule': crontab(minute=15, hour='*/2'),  # 15 min after ingestion
    },
    'trigger-high-risk-alerts': {
        'task': 'core.tasks.trigger_high_risk_alerts',
        'schedule': crontab(minute=20, hour='*/2'),  # 20 min after prediction
    },
    'send-daily-authority-digest': {
        'task': 'core.tasks.send_authority_daily_digest',
        'schedule': crontab(hour=8, minute=0),  # 8 AM daily
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
