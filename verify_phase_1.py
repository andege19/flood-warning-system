"""
Quick verification script for Phase 1 completion
Run: python verify_phase_1.py
"""

import os
import sys
import django
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flood_warning_system.settings')
django.setup()

from django.conf import settings
from django.db import connection
from core.models import Ward, CustomUser, CrowdReport, WeatherDataLake
import psycopg2

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def check_postgresql():
    """Check PostgreSQL connection"""
    print_section("1. POSTGRESQL CONNECTION")
    
    try:
        conn = psycopg2.connect(
            dbname=settings.DATABASES['default']['NAME'],
            user=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT']
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        print("✓ PostgreSQL connection successful")
        print(f"  Database: {settings.DATABASES['default']['NAME']}")
        print(f"  User: {settings.DATABASES['default']['USER']}")
        print(f"  Host: {settings.DATABASES['default']['HOST']}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ PostgreSQL connection failed: {e}")
        return False

def check_migrations():
    """Check if all migrations are applied"""
    print_section("2. DATABASE MIGRATIONS")
    
    try:
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        call_command('showmigrations', '--list', stdout=out)
        output = out.getvalue()
        
        if '[X]' in output:
            print("✓ Migrations applied")
            # Count applied vs unapplied
            applied = output.count('[X]')
            unapplied = output.count('[ ]')
            print(f"  Applied: {applied}")
            print(f"  Pending: {unapplied}")
            return unapplied == 0
        else:
            print("✗ No migrations found")
            return False
    except Exception as e:
        print(f"✗ Error checking migrations: {e}")
        return False

def check_models():
    """Check if models can be accessed"""
    print_section("3. DATABASE MODELS")
    
    try:
        ward_count = Ward.objects.count()
        user_count = CustomUser.objects.count()
        report_count = CrowdReport.objects.count()
        
        print(f"✓ Models accessible")
        print(f"  Wards: {ward_count}")
        print(f"  Users: {user_count}")
        print(f"  Reports: {report_count}")
        return True
    except Exception as e:
        print(f"✗ Error accessing models: {e}")
        return False

def check_email_config():
    """Check email configuration"""
    print_section("4. EMAIL CONFIGURATION")
    
    try:
        email_backend = settings.EMAIL_BACKEND
        print(f"✓ Email backend: {email_backend}")
        
        if 'console' in email_backend:
            print("  Mode: Development (Console)")
        elif 'anymail' in email_backend:
            print("  Mode: Production (Brevo)")
            
        brevo_key = settings.ANYMAIL.get('BREVO_API_KEY', '')
        if brevo_key:
            masked_key = brevo_key[:20] + '...' if len(brevo_key) > 20 else brevo_key
            print(f"  Brevo API Key: {masked_key}")
        
        print(f"  From Email: {settings.DEFAULT_FROM_EMAIL}")
        print(f"  Site URL: {settings.SITE_URL}")
        return True
    except Exception as e:
        print(f"✗ Error in email config: {e}")
        return False

def check_celery_config():
    """Check Celery configuration"""
    print_section("5. CELERY CONFIGURATION")
    
    try:
        broker = settings.CELERY_BROKER_URL
        backend = settings.CELERY_RESULT_BACKEND
        
        print(f"✓ Celery configured")
        print(f"  Broker: {broker}")
        print(f"  Backend: {backend}")
        print(f"  Timezone: {settings.CELERY_TIMEZONE}")
        return 'redis' in broker
    except Exception as e:
        print(f"✗ Error in Celery config: {e}")
        return False

def check_email_service():
    """Check email service module"""
    print_section("6. EMAIL SERVICE MODULE")
    
    try:
        from core.services.email_service import FloodAlertEmailService
        
        print("✓ Email service module imported successfully")
        print(f"  Class: FloodAlertEmailService")
        print(f"  Methods:")
        methods = ['send_flood_alert', 'send_report_confirmation', 
                  'send_report_validated', 'send_authority_notification']
        for method in methods:
            if hasattr(FloodAlertEmailService, method):
                print(f"    ✓ {method}")
        return True
    except Exception as e:
        print(f"✗ Error importing email service: {e}")
        return False

def check_templates():
    """Check email templates"""
    print_section("7. EMAIL TEMPLATES")
    
    templates_path = Path('templates/emails')
    templates = [
        'flood_alert.html',
        'report_confirmation.html',
        'report_validated.html',
        'authority_digest.html'
    ]
    
    all_exist = True
    for template in templates:
        path = templates_path / template
        if path.exists():
            print(f"✓ {template}")
        else:
            print(f"✗ {template} - NOT FOUND")
            all_exist = False
    
    return all_exist

def check_logging():
    """Check logging configuration"""
    print_section("8. LOGGING CONFIGURATION")
    
    try:
        logs_path = Path('logs')
        
        if logs_path.exists():
            print(f"✓ Logs directory exists")
            log_files = list(logs_path.glob('*.log'))
            print(f"  Log files: {len(log_files)}")
            for log_file in log_files[:5]:
                print(f"    - {log_file.name}")
        else:
            print(f"✗ Logs directory not found")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Error checking logging: {e}")
        return False

def main():
    """Run all verification checks"""
    print("\n" + "="*70)
    print("  PHASE 1 VERIFICATION SCRIPT")
    print("  Flood Warning System - MVP Upgrade")
    print("="*70)
    
    checks = [
        ("PostgreSQL Connection", check_postgresql),
        ("Database Migrations", check_migrations),
        ("Database Models", check_models),
        ("Email Configuration", check_email_config),
        ("Celery Configuration", check_celery_config),
        ("Email Service Module", check_email_service),
        ("Email Templates", check_templates),
        ("Logging Configuration", check_logging),
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"\n✗ Unexpected error: {e}")
            results.append((check_name, False))
    
    # Summary
    print_section("VERIFICATION SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    percentage = (passed / total) * 100
    
    print(f"Checks Passed: {passed}/{total} ({percentage:.0f}%)\n")
    
    for check_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {check_name}")
    
    print("\n" + "="*70)
    
    if percentage == 100:
        print("  ✓ PHASE 1 VERIFICATION: COMPLETE")
        print("  Ready to proceed to Phase 2: Enhanced Data Ingestion")
    elif percentage >= 80:
        print("  ⚠ PHASE 1 VERIFICATION: MOSTLY COMPLETE")
        print("  Fix failed items and re-run verification")
    else:
        print("  ✗ PHASE 1 VERIFICATION: INCOMPLETE")
        print("  Multiple issues found - review carefully")
    
    print("="*70 + "\n")
    
    return percentage == 100

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
