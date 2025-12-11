from django.core.management.base import BaseCommand
from core.models import HistoricalFloodEvent, FloodHistoricalData, ClimatePatternData
from django.db.models import Count

class Command(BaseCommand):
    help = 'Clean duplicate historical flood data'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n>>> Cleaning Duplicate Data\n'))
        
        # 1. Clean duplicate HistoricalFloodEvent
        self.stdout.write('Checking HistoricalFloodEvent duplicates...')
        
        duplicates = HistoricalFloodEvent.objects.values(
            'event_name', 'date_occurred'
        ).annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        deleted_events = 0
        for dup in duplicates:
            events = HistoricalFloodEvent.objects.filter(
                event_name=dup['event_name'],
                date_occurred=dup['date_occurred']
            ).order_by('id')
            
            # Keep the first, delete the rest
            for event in events[1:]:
                event.delete()
                deleted_events += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Removed {deleted_events} duplicate events'))
        
        # 2. Clean duplicate FloodHistoricalData (by ward+year)
        self.stdout.write('Checking FloodHistoricalData duplicates...')
        
        duplicates = FloodHistoricalData.objects.values(
            'ward', 'year'
        ).annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        deleted_hist = 0
        for dup in duplicates:
            records = FloodHistoricalData.objects.filter(
                ward=dup['ward'],
                year=dup['year']
            ).order_by('id')
            
            for record in records[1:]:
                record.delete()
                deleted_hist += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Removed {deleted_hist} duplicate historical data'))
        
        # 3. Clean duplicate ClimatePatternData (by ward+month+year)
        self.stdout.write('Checking ClimatePatternData duplicates...')
        
        duplicates = ClimatePatternData.objects.values(
            'ward', 'month', 'year'
        ).annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        deleted_climate = 0
        for dup in duplicates:
            records = ClimatePatternData.objects.filter(
                ward=dup['ward'],
                month=dup['month'],
                year=dup['year']
            ).order_by('id')
            
            for record in records[1:]:
                record.delete()
                deleted_climate += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Removed {deleted_climate} duplicate climate data'))
        
        # Summary
        total_removed = deleted_events + deleted_hist + deleted_climate
        self.stdout.write(self.style.SUCCESS(f'\n>>> Total duplicates removed: {total_removed}\n'))
        
        # Show current counts
        self.stdout.write('Current data counts:')
        self.stdout.write(f'  Historical Events: {HistoricalFloodEvent.objects.count()}')
        self.stdout.write(f'  Historical Data:   {FloodHistoricalData.objects.count()}')
        self.stdout.write(f'  Climate Patterns:  {ClimatePatternData.objects.count()}')
        self.stdout.write('')
