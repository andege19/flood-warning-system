from django.core.management.base import BaseCommand
from core.models import HistoricalFloodEvent, Ward
from datetime import datetime

class Command(BaseCommand):
    help = 'Import historical Nairobi flood data (2015-2025) - prevents duplicates'
    
    HISTORICAL_FLOODS = [
        {
            'event_name': 'April 2018 Heavy Rains',
            'date': '2018-04-15',
            'description': 'Severe flooding affected multiple Nairobi wards due to heavy rainfall over 3 days.',
            'risk_level': 'High',
            'rainfall_mm': 120,
            'temperature': 22,
            'humidity': 85,
            'wards': ['Kibra', 'Mathare', 'Kawangware'],
            'casualties': 15,
            'displaced': 2500,
            'damage': 5000000,
            'cause': 'heavy_rainfall',
            'source': 'NDMA Report 2018',
        },
        {
            'event_name': 'November 2019 Flash Floods',
            'date': '2019-11-22',
            'description': 'Flash floods in low-lying areas caused by sudden heavy rainfall.',
            'risk_level': 'High',
            'rainfall_mm': 95,
            'temperature': 24,
            'humidity': 80,
            'wards': ['Embakasi', 'Dandora', 'Kayole'],
            'casualties': 8,
            'displaced': 1800,
            'damage': 3500000,
            'cause': 'poor_drainage',
            'source': 'News Reports',
        },
        {
            'event_name': 'March 2020 Seasonal Rains',
            'date': '2020-03-18',
            'description': 'Long rains caused widespread flooding in informal settlements.',
            'risk_level': 'Medium',
            'rainfall_mm': 85,
            'temperature': 21,
            'humidity': 75,
            'wards': ['Kibra', 'Westlands', 'Mathare'],
            'casualties': 5,
            'displaced': 1200,
            'damage': 2000000,
            'cause': 'heavy_rainfall',
            'source': 'NDMA Report',
        },
        {
            'event_name': 'April 2022 Flooding',
            'date': '2022-04-10',
            'description': 'Heavy rains combined with poor drainage systems caused major flooding.',
            'risk_level': 'High',
            'rainfall_mm': 110,
            'temperature': 23,
            'humidity': 82,
            'wards': ['Embakasi', 'Huruma', 'Kawangware'],
            'casualties': 12,
            'displaced': 3000,
            'damage': 6000000,
            'cause': 'poor_infrastructure',
            'source': 'NDMA & Media',
        },
    ]
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Delete existing events and reimport'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n>>> Importing Historical Flood Data\n'))
        
        # Optional: Clear existing data
        if options.get('force'):
            count = HistoricalFloodEvent.objects.count()
            HistoricalFloodEvent.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Deleted {count} existing events'))
        
        imported = 0
        skipped = 0
        
        for flood_data in self.HISTORICAL_FLOODS:
            try:
                # Check if event already exists (by name and date)
                existing = HistoricalFloodEvent.objects.filter(
                    event_name=flood_data['event_name'],
                    date_occurred=datetime.strptime(flood_data['date'], '%Y-%m-%d').date()
                ).first()
                
                if existing:
                    self.stdout.write(self.style.WARNING(f'⊘ Skipped (exists): {flood_data["event_name"]}'))
                    skipped += 1
                    continue
                
                # Create event
                event = HistoricalFloodEvent.objects.create(
                    event_name=flood_data['event_name'],
                    description=flood_data['description'],
                    date_occurred=datetime.strptime(flood_data['date'], '%Y-%m-%d'),
                    risk_level=flood_data['risk_level'],
                    rainfall_mm=flood_data['rainfall_mm'],
                    temperature_celsius=flood_data['temperature'],
                    humidity_percent=flood_data['humidity'],
                    estimated_casualties=flood_data['casualties'],
                    estimated_displaced=flood_data['displaced'],
                    estimated_damage_value=flood_data['damage'],
                    primary_cause=flood_data['cause'],
                    data_source=flood_data['source'],
                    latitude=-1.28,
                    longitude=36.82,
                )
                
                # Add affected wards
                for ward_name in flood_data['wards']:
                    ward = Ward.objects.filter(name__icontains=ward_name).first()
                    if ward:
                        event.affected_wards.add(ward)
                
                self.stdout.write(self.style.SUCCESS(f'✓ Imported: {flood_data["event_name"]}'))
                imported += 1
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Error: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n>>> Imported: {imported}, Skipped: {skipped}\n'))
