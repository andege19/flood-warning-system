"""
Test script to send real emails via Brevo (Production Mode)
Run: python test_email_production.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flood_warning_system.settings')
django.setup()

from core.services.email_service import FloodAlertEmailService
from django.conf import settings

def main():
    print("=" * 70)
    print("EMAIL SYSTEM TEST - PRODUCTION MODE")
    print("=" * 70)
    print(f"\nEmail Backend: {settings.EMAIL_BACKEND}")
    print(f"From Email: {settings.DEFAULT_FROM_EMAIL}")
    print(f"Brevo API Key: {'✓ Configured' if settings.ANYMAIL.get('BREVO_API_KEY') else '✗ Missing'}")
    print(f"Site URL: {settings.SITE_URL}")
    print("\n" + "=" * 70)
    
    # Test 1: Flood Alert
    print("\n[TEST 1] Sending Flood Alert Email...")
    print("-" * 70)
    
    result1 = FloodAlertEmailService.send_flood_alert(
        recipient_email='alicedeborah45@gmail.com',  # Change this to your email
        recipient_name='Alice Deborah',
        ward_name='Kibera',
        risk_level='High',
        details={
            'forecast': 'Heavy rainfall expected within 24 hours',
            'rainfall': '120mm'
        }
    )
    
    if result1:
        print("Flood alert email sent successfully!")
        print("  Check your email inbox (may take a few seconds)")
    else:
        print("Failed to send flood alert")
    
    # Test 2: Report Confirmation
    print("\n[TEST 2] Sending Report Confirmation Email...")
    print("-" * 70)
    
    result2 = FloodAlertEmailService.send_report_confirmation(
        recipient_email='alicedeborah45@gmail.com',  # Change this to your email
        recipient_name='Test User',
        report_id=999,
        location='Test Location'
    )
    
    if result2:
        print("Report confirmation email sent successfully!")
        print("Check your email inbox")
    else:
        print("Failed to send report confirmation")
    
    print("\n" + "=" * 70)
    print("IMPORTANT: Check your Brevo dashboard for delivery status")
    print("Dashboard: https://app.brevo.com")
    print("=" * 70)

if __name__ == '__main__':
    main()
