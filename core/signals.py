from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
from core.models import WeatherDataLake, Ward, Alert
import logging

logger = logging.getLogger(__name__)

# This is a "mock" function to simulate sending an SMS
# Later, this will call the Twilio API
def send_twilio_alert(phone_number, message):
    print("--------------------------------------------------")
    print(f"SIMULATING SMS/WHATSAPP ALERT to {phone_number}:")
    print(message)
    print("--------------------------------------------------")
  

# use of 'pre_save' to check the *old* value before it's saved
@receiver(pre_save, sender=Ward)
def check_risk_level_change(sender, instance, **kwargs):
    """
    Listens for a change in a Ward's risk level.
    If it changes TO 'High', send alerts.
    """
    if instance.pk is None:
        # This is a new ward, do nothing
        return

    try:
        # Get the "old" ward data from the database
        old_ward = Ward.objects.get(pk=instance.pk)
    except Ward.DoesNotExist:
        return # Should not happen, but good to check

    # Check if the risk level is changing *from* something else *to* 'High'
    old_risk = old_ward.current_risk_level
    new_risk = instance.current_risk_level
    
    if new_risk == 'High' and old_risk != 'High':
        # The risk level just escalated to HIGH!
        # Find all users subscribed to this ward
        subscribers = instance.subscribers.all()
        
        message = f"!! FLOOD ALERT !! High flood risk detected for {instance.name}. Please take necessary precautions and move to higher ground."
        
        # 1. Log this alert in our database
        Alert.objects.create(
            ward=instance,
            risk_level='High',
            message_text=message
        )
        
        # 2. Send the "SMS" to every subscriber
        for user in subscribers:
            if user.phone_number:
                send_twilio_alert(user.phone_number, message)

"""
PHASE 2: Risk Engine
Listens for new RawWeatherData and processes it to update Ward risk levels.
This is decoupled from data ingestion for resilience.
"""

@receiver(post_save, sender=WeatherDataLake)
def process_weather_data(sender, instance, created, **kwargs):
    """
    Process newly ingested weather data
    """
    if created:
        try:
            # RISK ENGINE LOGIC
            rainfall = instance.rainfall_mm
            ward = instance.ward

            # Simple rules (Phase 1 ML)
            # In Phase 3, this will call a real scikit-learn/TensorFlow model
            if rainfall > ward.rain_threshold_mm:
                new_risk = 'High'
            elif rainfall > (ward.rain_threshold_mm / 2):
                new_risk = 'Medium'
            else:
                new_risk = 'Low'

            # Store the forecasted risk in RawWeatherData for historical record
            instance.forecasted_risk_level = new_risk
            instance.processed_at = timezone.now()
            instance.save(update_fields=['forecasted_risk_level', 'processed_at'])

            # Update the Ward's current risk level
            if ward.current_risk_level != new_risk:
                ward.current_risk_level = new_risk
                ward.save(update_fields=['current_risk_level'])

                logger.info(f"[Risk Engine] {ward.name}: {rainfall}mm → Risk changed to {new_risk}")
        except Exception as e:
            logger.error(f"Error processing weather data: {str(e)}")
