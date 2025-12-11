from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from core.services.email_service import FloodAlertEmailService
from core.models import CrowdReport, CustomUser

class Command(BaseCommand):
    help = 'Complete email testing for all email types'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            type=str,
            help='Email address to send test emails to'
        )
    
    def handle(self, *args, **options):
        recipient = options['email']
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write('COMPLETE EMAIL SYSTEM TEST')
        self.stdout.write('='*60)
        self.stdout.write(f'Configuration:')
        self.stdout.write(f'  Backend: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'  From: {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write(f'  To: {recipient}')
        self.stdout.write('='*60 + '\n')
        
        tests_passed = 0
        tests_failed = 0
        
        # Test 1: Simple Email
        self.stdout.write('Test 1: Simple Email')
        try:
            send_mail(
                subject='Flood Warning System - Test Email',
                message='This is a test email. If you received this, the email system is working!',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS('  PASSED: Simple email sent'))
            tests_passed += 1
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  FAILED: {str(e)}'))
            tests_failed += 1
        
        # Test 2: Report Confirmation Email
        self.stdout.write('\nTest 2: Report Confirmation Email')
        try:
            success = FloodAlertEmailService.send_report_confirmation(
                recipient_email=recipient,
                recipient_name='Test User',
                report_id=12345,
                location='Westlands Ward'
            )
            if success:
                self.stdout.write(self.style.SUCCESS('  PASSED: Report confirmation sent'))
                tests_passed += 1
            else:
                self.stdout.write(self.style.ERROR('  FAILED: Report confirmation not sent'))
                tests_failed += 1
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  FAILED: {str(e)}'))
            tests_failed += 1
        
        # Test 3: Report Validated Email
        self.stdout.write('\nTest 3: Report Validated Email')
        try:
            success = FloodAlertEmailService.send_report_validated(
                recipient_email=recipient,
                recipient_name='Test User',
                report_id=12345
            )
            if success:
                self.stdout.write(self.style.SUCCESS('  PASSED: Report validated email sent'))
                tests_passed += 1
            else:
                self.stdout.write(self.style.ERROR('  FAILED: Report validated email not sent'))
                tests_failed += 1
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  FAILED: {str(e)}'))
            tests_failed += 1
        
        # Test 4: Report Rejected Email
        self.stdout.write('\nTest 4: Report Rejected Email')
        try:
            success = FloodAlertEmailService.send_report_rejected(
                recipient_email=recipient,
                recipient_name='Test User',
                report_id=12345
            )
            if success:
                self.stdout.write(self.style.SUCCESS('  PASSED: Report rejected email sent'))
                tests_passed += 1
            else:
                self.stdout.write(self.style.ERROR('  FAILED: Report rejected email not sent'))
                tests_failed += 1
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  FAILED: {str(e)}'))
            tests_failed += 1
        
        # Test 5: Flood Alert Email
        self.stdout.write('\nTest 5: Flood Alert Email')
        try:
            success = FloodAlertEmailService.send_flood_alert(
                recipient_email=recipient,
                recipient_name='Test User',
                ward_name='Kibra',
                risk_level='High',
                alert_message='This is a TEST flood alert. No action required.'
            )
            if success:
                self.stdout.write(self.style.SUCCESS('  PASSED: Flood alert email sent'))
                tests_passed += 1
            else:
                self.stdout.write(self.style.ERROR('  FAILED: Flood alert email not sent'))
                tests_failed += 1
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  FAILED: {str(e)}'))
            tests_failed += 1
        
        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write('TEST SUMMARY')
        self.stdout.write('='*60)
        self.stdout.write(self.style.SUCCESS(f'Passed: {tests_passed}'))
        if tests_failed > 0:
            self.stdout.write(self.style.ERROR(f'Failed: {tests_failed}'))
        self.stdout.write('='*60 + '\n')
        
        if tests_failed == 0:
            self.stdout.write(self.style.SUCCESS('All tests passed! Email system is working correctly.'))
        else:
            self.stdout.write(self.style.ERROR('Some tests failed. Check the errors above.'))
