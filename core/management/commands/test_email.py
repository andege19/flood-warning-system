from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from core.services.email_service import FloodAlertEmailService

class Command(BaseCommand):
    help = 'Test email configuration with Resend'
    
    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email to test')
    
    def handle(self, *args, **options):
        recipient = options['email']
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write('EMAIL CONFIGURATION TEST - RESEND')
        self.stdout.write('='*60)
        self.stdout.write(f'Backend: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'From: {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write(f'Domain: floodwarning.biz')
        self.stdout.write(f'To: {recipient}')
        self.stdout.write('='*60 + '\n')
        
        try:
            # Test 1: Simple email
            self.stdout.write('Test 1: Simple test email...')
            send_mail(
                subject='Flood Warning System - Configuration Test',
                message='This is a test email from your Resend domain floodwarning.biz',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS('  SUCCESS: Simple email sent!'))
            
            # Test 2: Report confirmation
            self.stdout.write('\nTest 2: Report confirmation email...')
            success = FloodAlertEmailService.send_report_confirmation(
                recipient_email=recipient,
                recipient_name='Test User',
                report_id=999,
                location='Test Location'
            )
            if success:
                self.stdout.write(self.style.SUCCESS('  SUCCESS: Report confirmation sent!'))
            
            # Test 3: Validated email
            self.stdout.write('\nTest 3: Report validated email...')
            success = FloodAlertEmailService.send_report_validated(
                recipient_email=recipient,
                recipient_name='Test User',
                report_id=999,
                admin_message='Thank you for your contribution!'
            )
            if success:
                self.stdout.write(self.style.SUCCESS('  SUCCESS: Validation email sent!'))
            
            # Test 4: Flood alert
            self.stdout.write('\nTest 4: Flood alert email...')
            success = FloodAlertEmailService.send_flood_alert(
                recipient_email=recipient,
                recipient_name='Test User',
                ward_name='Westlands',
                risk_level='High',
                alert_message='This is a TEST flood alert for testing purposes.'
            )
            if success:
                self.stdout.write(self.style.SUCCESS('  SUCCESS: Flood alert sent!'))
            
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.SUCCESS(f'All tests passed! Check {recipient}'))
            self.stdout.write('='*60 + '\n')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nERROR: {str(e)}'))
            self.stdout.write('\nCheck:')
            self.stdout.write('1. RESEND_API_KEY in .env')
            self.stdout.write('2. Domain verified in Resend')
            self.stdout.write('3. USE_CONSOLE_EMAIL=False')
