"""
Test script for email configuration
Run: python test_email.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flood_warning_system.settings')
django.setup()

from core.services.email_service import FloodAlertEmailService
from django.conf import settings

def test_flood_alert_email():
    """Test flood alert email"""
    print("Testing flood alert email...")
    
    result = FloodAlertEmailService.send_flood_alert(
        recipient_email='test@example.com',
        recipient_name='John Doe',
        ward_name='Kibera',
        risk_level='High',
        details={
            'forecast': 'Heavy rainfall expected',
            'rainfall': '120mm'
        }
    )
    
    if result:
        print("✓ Flood alert email sent successfully!")
    else:
        print("✗ Failed to send flood alert email")
    
    return result


def test_report_confirmation():
    """Test report confirmation email"""
    print("Testing report confirmation email...")
    
    result = FloodAlertEmailService.send_report_confirmation(
        recipient_email='reporter@example.com',
        recipient_name='Jane Smith',
        report_id=123,
        location='Corner of Main St'
    )
    
    if result:
        print("✓ Report confirmation email sent successfully!")
    else:
        print("✗ Failed to send report confirmation")
    
    return result


if __name__ == '__main__':
    print(f"Email Backend: {settings.EMAIL_BACKEND}")
    print(f"Default From Email: {settings.DEFAULT_FROM_EMAIL}")
    print()
    
    print("=" * 50)
    test_flood_alert_email()
    print("=" * 50)
    test_report_confirmation()
    print("=" * 50)
    
    print("\nIf emails appear in console, you're using development mode.")
    print("Set EMAIL_BACKEND to 'anymail.backends.brevo.EmailBackend' in settings.py to use Brevo.")
