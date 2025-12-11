from django.core.management.base import BaseCommand
from core.services.data_pipeline import DataPipeline
from core.ml_model import FloodRiskMLModel
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run all system tasks sequentially (data ingestion + ML prediction + alerts)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-ingestion',
            action='store_true',
            help='Skip data ingestion, only run predictions'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('FLOOD WARNING SYSTEM - COMPLETE TASK RUN'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        
        try:
            # Step 1: Ingest weather data
            if not options['skip_ingestion']:
                self.stdout.write(self.style.WARNING('1. Ingesting weather data from multiple sources...'))
                result = DataPipeline.ingest_all_data()
                self.stdout.write(self.style.SUCCESS(
                    f'   ✓ {result["total_records"]} records ingested\n'
                ))
            else:
                self.stdout.write(self.style.WARNING('1. Skipping data ingestion\n'))
            
            # Step 2: Train ML model
            self.stdout.write(self.style.WARNING('2. Training ML model...'))
            if FloodRiskMLModel.train_model(force=False):
                self.stdout.write(self.style.SUCCESS('   ✓ Model ready\n'))
            else:
                self.stdout.write(self.style.ERROR('   ✗ Model training issue\n'))
            
            # Step 3: Predict flood risk
            self.stdout.write(self.style.WARNING('3. Predicting flood risk for all wards...'))
            predictions = FloodRiskMLModel.predict_all_wards()
            self.stdout.write(self.style.SUCCESS(
                f'   ✓ {predictions} predictions created\n'
            ))
            
            # Step 4: Verify predictions
            from core.models import FloodPrediction, Ward
            self.stdout.write(self.style.WARNING('4. Current Risk Levels:'))
            for ward in Ward.objects.all():
                latest = FloodPrediction.objects.filter(ward=ward).order_by('-created_at').first()
                if latest:
                    confidence = f"{latest.confidence_score:.0%}"
                    self.stdout.write(f'   {ward.name}: {latest.predicted_risk_level} ({confidence})')
            
            self.stdout.write('\n' + self.style.SUCCESS('='*70))
            self.stdout.write(self.style.SUCCESS('ALL TASKS COMPLETED SUCCESSFULLY'))
            self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nERROR: {str(e)}\n'))
