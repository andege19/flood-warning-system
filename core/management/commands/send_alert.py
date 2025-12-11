from django.core.management.base import BaseCommand
from core.models import Ward, CustomUser
from core.services.email_service import FloodAlertEmailService

class Command(BaseCommand):
    help = 'Send flood alerts to users for specific wards'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--ward',
            type=str,
            help='Ward ID or name'
        )
        parser.add_argument(
            '--risk-level',
            type=str,
            choices=['High', 'Medium', 'Low'],
            default='High',
            help='Risk level'
        )
        parser.add_argument(
            '--message',
            type=str,
            help='Custom alert message'
        )
    
    def handle(self, *args, **options):
        ward_id = options.get('ward')
        risk_level = options.get('risk_level')
        custom_message = options.get('message')
        
        if not ward_id:
            self.stdout.write(self.style.ERROR('Please specify --ward'))
            return
        
        try:
            ward = Ward.objects.get(id=int(ward_id))
        except Ward.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Ward #{ward_id} not found'))
            return
        
        # Get all active users
        users = CustomUser.objects.filter(
            is_active=True,
            email__isnull=False
        ).exclude(email='')
        
        message = custom_message or f"Flood alert: {risk_level} risk reported in {ward.name}"
        
        self.stdout.write(f'\nSending alerts for {ward.name} ({risk_level} Risk)...')
        self.stdout.write(f'Message: {message}')
        self.stdout.write(f'Recipients: {users.count()} users\n')
        
        sent_count = 0
        failed_count = 0
        
        for user in users:
            try:
                success = FloodAlertEmailService.send_flood_alert(
                    recipient_email=user.email,
                    recipient_name=user.username,
                    ward_name=ward.name,
                    risk_level=risk_level,
                    alert_message=message
                )
                
                if success:
                    self.stdout.write(f'  Sent to {user.email}')
                    sent_count += 1
                else:
                    self.stdout.write(self.style.WARNING(f'  Failed: {user.email}'))
                    failed_count += 1
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error: {user.email} - {str(e)}'))
                failed_count += 1
        
        self.stdout.write(f'\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'Sent: {sent_count}'))
        if failed_count > 0:
            self.stdout.write(self.style.ERROR(f'Failed: {failed_count}'))
        self.stdout.write('='*50 + '\n')
