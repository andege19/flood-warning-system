"""
Management command for weather data ingestion
Usage: python manage.py ingest_weather_data [--backfill N]
"""

from django.core.management.base import BaseCommand, CommandError
from core.services.data_pipeline import DataPipeline
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Ingest weather data from multiple sources'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--backfill',
            type=int,
            help='Number of days to backfill historical data'
        )
        
        parser.add_argument(
            '--status',
            action='store_true',
            help='Show current data status'
        )
    
    def handle(self, *args, **options):
        try:
            if options['status']:
                self._show_status()
            elif options['backfill']:
                self._backfill_data(options['backfill'])
            else:
                self._ingest_current_data()
        
        except Exception as e:
            raise CommandError(f'Error: {str(e)}')
    
    def _ingest_current_data(self):
        """Ingest current weather data"""
        self.stdout.write(self.style.SUCCESS('\n>>> Starting Weather Data Ingestion\n'))
        
        result = DataPipeline.ingest_all_data()
        
        self.stdout.write(self.style.SUCCESS(f'✓ Total Records Stored: {result["total_records"]}'))
        
        for source, status in result['sources'].items():
            if status['success']:
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ {source}: {status["records"]} records')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ {source}: {status.get("error", "Unknown error")}')
                )
        
        self.stdout.write(self.style.SUCCESS('\n>>> Ingestion Complete\n'))
    
    def _backfill_data(self, days):
        """Backfill historical data"""
        self.stdout.write(self.style.SUCCESS(f'\n>>> Starting {days}-Day Backfill\n'))
        
        result = DataPipeline.backfill_historical_data(days=days)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Total Records: {result["total_records"]}'))
        self.stdout.write(self.style.SUCCESS('\n>>> Backfill Complete\n'))
    
    def _show_status(self):
        """Show current data status"""
        self.stdout.write(self.style.SUCCESS('\n>>> Data Ingestion Status\n'))
        
        status = DataPipeline.get_latest_data_status()
        
        self.stdout.write(f'Status: {status["status"]}')
        self.stdout.write(f'Last Update: {status["last_update"]}')
        self.stdout.write(f'Total Records: {status["records"]}')
        
        if status.get('sources'):
            self.stdout.write('Sources:')
            for source in status['sources']:
                self.stdout.write(f'  - {source["source"]}')
        
        self.stdout.write(self.style.SUCCESS('\n'))
