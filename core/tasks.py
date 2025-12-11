"""
Celery tasks for background email processing and data ingestion
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from core.models import Ward, FloodPrediction, CrowdReport, CustomUser
from core.services.email_service import FloodAlertEmailService
from core.services.data_pipeline import DataPipeline
from core.ml_model import FloodRiskMLModel
from core.ml_model_advanced import AdvancedFloodRiskMLModel
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_flood_alert_emails(ward_id, risk_level, details=None):
    """
    Background task to send flood alert emails
    """
    try:
        ward = Ward.objects.get(id=ward_id)
        
        # Get subscribers
        subscribers = ward.subscribers.all()
        recipients = [(u.email, u.username) for u in subscribers if u.email]
        
        if recipients:
            result = FloodAlertEmailService.send_bulk_alerts(
                recipients=recipients,
                ward_name=ward.name,
                risk_level=risk_level,
                details=details
            )
            logger.info(f"Sent flood alerts to {result['success']} users")
            return result
    
    except Ward.DoesNotExist:
        logger.error(f"Ward {ward_id} not found")
        return {'success': 0, 'failed': 0}
    except Exception as e:
        logger.error(f"Error in send_flood_alert_emails: {e}")
        return {'success': 0, 'failed': 0}


@shared_task
def send_authority_daily_digest():
    """
    Background task to send daily digest to authorities
    """
    try:
        # Get all authority users
        authorities = CustomUser.objects.filter(role='authority')
        
        for authority in authorities:
            if not authority.email:
                continue
            
            # Count pending reports
            pending_count = CrowdReport.objects.filter(
                status='Pending'
            ).count()
            
            # Count recent alerts
            alert_count = FloodPrediction.objects.filter(
                predicted_risk_level='High',
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).count()
            
            # Send digest
            FloodAlertEmailService.send_authority_notification(
                recipient_email=authority.email,
                recipient_name=authority.username,
                alert_count=alert_count,
                pending_reports=pending_count
            )
        
        logger.info(f"Sent daily digest to {authorities.count()} authorities")
    
    except Exception as e:
        logger.error(f"Error in send_authority_daily_digest: {e}")


@shared_task
def ingest_weather_data():
    """
    Background task for weather data ingestion
    Runs every 1-2 hours via Celery Beat
    """
    try:
        result = DataPipeline.ingest_all_data()
        logger.info(f"Weather data ingestion completed: {result['total_records']} records")
        return result
    except Exception as e:
        logger.error(f"Error in ingest_weather_data: {str(e)}")
        return {'error': str(e)}


@shared_task
def backfill_weather_data(days=7):
    """
    Background task to backfill historical weather data
    Run manually: python manage.py ingest_weather_data --backfill 7
    """
    try:
        result = DataPipeline.backfill_historical_data(days=days)
        logger.info(f"Weather data backfill completed: {result['total_records']} records")
        return result
    except Exception as e:
        logger.error(f"Error in backfill_weather_data: {str(e)}")
        return {'error': str(e)}


@shared_task
def predict_flood_risk():
    """
    Background task for ML model predictions
    Runs every 2 hours via Celery Beat
    """
    try:
        logger.info("Starting flood risk prediction...")
        
        # Train model if needed
        FloodRiskMLModel.train_model(force=False)
        
        # Predict for all wards
        predictions = FloodRiskMLModel.predict_all_wards()
        
        logger.info(f"Flood risk prediction completed: {predictions} wards")
        return {'predictions': predictions, 'status': 'success'}
    
    except Exception as e:
        logger.error(f"Error in predict_flood_risk: {str(e)}")
        return {'error': str(e), 'status': 'failed'}


@shared_task
def predict_flood_risk_advanced():
    """
    Advanced prediction task with 97-100% confidence
    Runs every 2 hours via Celery Beat
    """
    try:
        logger.info("Starting advanced flood risk prediction...")
        
        # Train model if needed
        AdvancedFloodRiskMLModel.train_advanced_model(force=False)
        
        # Predict for all Nairobi wards
        predictions = AdvancedFloodRiskMLModel.predict_all_nairobi_wards()
        
        logger.info(f"Advanced prediction completed: {predictions} wards")
        return {'predictions': predictions, 'status': 'success', 'model': 'v3.0-advanced'}
    
    except Exception as e:
        logger.error(f"Error in predict_flood_risk_advanced: {str(e)}")
        return {'error': str(e), 'status': 'failed'}


@shared_task
def trigger_high_risk_alerts():
    """
    Trigger alerts for wards with high flood risk
    """
    try:
        from core.services.email_service import FloodAlertEmailService
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        recent_predictions = FloodPrediction.objects.filter(
            predicted_risk_level='High',
            created_at__gte=now - timedelta(hours=1)
        ).select_related('ward')
        
        alerts_sent = 0
        
        for prediction in recent_predictions:
            ward = prediction.ward
            subscribers = ward.subscribers.filter(email__isnull=False)
            
            if subscribers.exists():
                recipients = [
                    (user.email, user.username) 
                    for user in subscribers
                ]
                
                result = FloodAlertEmailService.send_bulk_alerts(
                    recipients=recipients,
                    ward_name=ward.name,
                    risk_level='High',
                    details={
                        'confidence': f"{prediction.confidence_score:.1%}",
                        'probability_high': f"{prediction.probability_high:.1%}"
                    }
                )
                
                if result['success'] > 0:
                    alerts_sent += result['success']
        
        logger.info(f"Sent {alerts_sent} high risk alerts")
        return {'alerts_sent': alerts_sent}
    
    except Exception as e:
        logger.error(f"Error triggering alerts: {str(e)}")
        return {'error': str(e)}
