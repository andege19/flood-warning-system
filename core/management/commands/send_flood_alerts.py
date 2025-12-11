from django.core.management.base import BaseCommand
from core.models import Ward, CustomUser
from core.services.email_service import FloodAlertEmailService

class Command(BaseCommand):
    help = 'Send flood alerts for high-risk wards'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--ward',
            type=str,
            help='Specific ward name to send alert for'
        )
        parser.add_argument(
            '--risk-level',
            type=str,
            choices=['High', 'Medium'],
            default='High',
            help='Minimum risk level to trigger alerts'
        )
        parser.add_argument(
            '--message',
            type=str,
            help='Custom alert message'
        )
    
    def handle(self, *args, **options):
        self.stdout.write('Sending flood alerts...')
        
        ward_name = options.get('ward')
        risk_level = options.get('risk_level') or 'High'
        custom_message = options.get('message')
        
        # Get wards to alert
        if ward_name:
            wards = Ward.objects.filter(name__icontains=ward_name)
        else:
            if risk_level == 'High':
                wards = Ward.objects.filter(current_risk_level='High')
            else:
                wards = Ward.objects.filter(current_risk_level__in=['High', 'Medium'])
        
        if not wards.exists():
            self.stdout.write(self.style.WARNING('No wards found matching criteria'))
            return
        
        # Get all active users with email
        users = CustomUser.objects.filter(
            is_active=True,
            email__isnull=False
        ).exclude(email='')
        
        total_sent = 0
        
        for ward in wards:
            message = custom_message or f"Flood risk is currently {ward.current_risk_level} in {ward.name}. Please take necessary precautions."
            
            self.stdout.write(f'\nSending alerts for {ward.name} ({ward.current_risk_level} Risk)...')
            
            for user in users:
                success = FloodAlertEmailService.send_flood_alert(
                    recipient_email=user.email,
                    recipient_name=user.username,
                    ward_name=ward.name,
                    risk_level=ward.current_risk_level,
                    alert_message=message
                )
                if success:
                    total_sent += 1
        
        self.stdout.write(self.style.SUCCESS(f'\nTotal alerts sent: {total_sent}'))
