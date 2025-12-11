from django.core.management.base import BaseCommand
from core.models import Ward
import json
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Load initial Nairobi wards data'
    
    WARDS = [
        {'name': 'Westlands', 'lat': -1.2761, 'lon': 36.8081},
        {'name': 'Kilimani', 'lat': -1.2920, 'lon': 36.7800},
        {'name': 'Karura', 'lat': -1.2528, 'lon': 36.7447},
        {'name': 'Kitisuru', 'lat': -1.2361, 'lon': 36.7567},
        {'name': 'Kabete', 'lat': -1.2817, 'lon': 36.6973},
        {'name': 'Ruai', 'lat': -1.3567, 'lon': 36.9392},
        {'name': 'Embakasi', 'lat': -1.3189, 'lon': 36.8995},
        {'name': 'Kamukunji', 'lat': -1.2921, 'lon': 36.8507},
        {'name': 'Starehe', 'lat': -1.2869, 'lon': 36.8447},
        {'name': 'Makadara', 'lat': -1.3089, 'lon': 36.8689},
        {'name': 'Mathare', 'lat': -1.2447, 'lon': 36.8456},
        {'name': 'Huruma', 'lat': -1.2689, 'lon': 36.8234},
        {'name': 'Roysambu', 'lat': -1.1867, 'lon': 36.8831},
        {'name': 'Kasarani', 'lat': -1.1908, 'lon': 36.9156},
        {'name': 'Nairobi Central', 'lat': -1.2865, 'lon': 36.8185},
        {'name': 'Nairobi East', 'lat': -1.2890, 'lon': 36.8621},
        {'name': 'Nairobi South', 'lat': -1.3192, 'lon': 36.7882},
        {'name': 'Nairobi West', 'lat': -1.3233, 'lon': 36.7447},
        {'name': 'Kibra', 'lat': -1.3145, 'lon': 36.7737},
        {'name': 'Kawangware', 'lat': -1.3678, 'lon': 36.7222},
        {'name': 'Langata', 'lat': -1.3892, 'lon': 36.7344},
        {'name': 'Dagoretti North', 'lat': -1.3456, 'lon': 36.6890},
        {'name': 'Dagoretti South', 'lat': -1.3678, 'lon': 36.6678},
        {'name': 'Waithaka', 'lat': -1.3456, 'lon': 36.6389},
        {'name': 'Riruta', 'lat': -1.3478, 'lon': 36.6145},
        {'name': 'Mutu-Ini', 'lat': -1.3800, 'lon': 36.5900},
        {'name': 'Geimbe', 'lat': -1.4100, 'lon': 36.5600},
        {'name': 'Imara Daima', 'lat': -1.3800, 'lon': 36.9200},
        {'name': 'Dandora', 'lat': -1.3345, 'lon': 36.9100},
        {'name': 'Laini Saba', 'lat': -1.3100, 'lon': 36.9000},
        {'name': 'Kayole', 'lat': -1.3467, 'lon': 36.9567},
        {'name': 'Soweto East', 'lat': -1.3650, 'lon': 36.9300},
        {'name': 'Soweto West', 'lat': -1.3678, 'lon': 36.9100},
    ]
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Delete existing wards and reload'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n>>> Loading Nairobi Wards\n'))
        
        # Optional: Delete existing wards
        if options['force']:
            count = Ward.objects.count()
            Ward.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Deleted {count} existing wards'))
        
        created_count = 0
        updated_count = 0
        
        for ward_data in self.WARDS:
            ward, created = Ward.objects.get_or_create(
                name=ward_data['name'],
                defaults={
                    'geom_json': json.dumps({
                        'type': 'Point',
                        'coordinates': [ward_data['lon'], ward_data['lat']]
                    }),
                    'population': 50000,
                    'current_risk_level': 'Low'
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Created: {ward.name}'))
            else:
                # Update if exists
                ward.geom_json = json.dumps({
                    'type': 'Point',
                    'coordinates': [ward_data['lon'], ward_data['lat']]
                })
                ward.save()
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'✓ Updated: {ward.name}'))
        
        total = Ward.objects.count()
        self.stdout.write(self.style.SUCCESS(f'\n>>> Created: {created_count}, Updated: {updated_count}'))
        self.stdout.write(self.style.SUCCESS(f'>>> Total wards in database: {total}\n'))
