from django.core.management.base import BaseCommand
from core.ml_model import FloodRiskMLModel
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Predict flood risk for all wards'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--train',
            action='store_true',
            help='Train model before predicting'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n>>> Starting Flood Risk Prediction\n'))
        
        # Train if requested
        if options['train']:
            self.stdout.write('Training model...')
            if FloodRiskMLModel.train_model(force=True):
                self.stdout.write(self.style.SUCCESS('Model trained successfully'))
            else:
                self.stdout.write(self.style.ERROR('Model training failed'))
        
        # Predict
        self.stdout.write('Predicting flood risk for all wards...')
        predictions = FloodRiskMLModel.predict_all_wards()
        
        self.stdout.write(self.style.SUCCESS(f'\nPredictions created: {predictions}'))
        self.stdout.write(self.style.SUCCESS('\n>>> Prediction Complete\n'))
