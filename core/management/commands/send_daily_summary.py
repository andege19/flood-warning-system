from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import CustomUser, CrowdReport, Ward
from core.services.email_service import FloodAlertEmailService

class Command(BaseCommand):
    help = 'Send daily summary email to all authority users'
    
    def handle(self, *args, **options):
        self.stdout.write('Sending daily summary emails...')
        
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        # Gather statistics
        stats = {
            'date': today.strftime('%B %d, %Y'),
            'pending': CrowdReport.objects.filter(status='Pending').count(),
            'validated': CrowdReport.objects.filter(
                status='Validated',
                created_at__date=yesterday
            ).count(),
            'high_risk': Ward.objects.filter(current_risk_level='High').count(),
            'medium_risk': Ward.objects.filter(current_risk_level='Medium').count(),
            'low_risk': Ward.objects.filter(current_risk_level='Low').count(),
        }
        
        # Get all authority users
        authorities = CustomUser.objects.filter(
            role='authority',
            is_active=True,
            email__isnull=False
        ).exclude(email='')
        
        sent_count = 0
        for authority in authorities:
            success = FloodAlertEmailService.send_daily_summary(
                authority_email=authority.email,
                authority_name=authority.username,
                stats=stats
            )
            if success:
                sent_count += 1
                self.stdout.write(f'  Sent to: {authority.email}')
        
        self.stdout.write(self.style.SUCCESS(f'Daily summary sent to {sent_count} authorities'))
