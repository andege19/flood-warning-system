from django.core.management.base import BaseCommand
from core.models import Ward, WeatherData
from core.ml_model import predict_flood_risk # Import our "AI Brain" function
import random

class Command(BaseCommand):
    help = 'Runs the ML model to predict flood risk for each ward.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting flood risk prediction...'))
        
        wards = Ward.objects.all()
        if not wards.exists():
            self.stdout.write(self.style.WARNING('No wards found. Please add wards in the admin panel.'))
            return

        for ward in wards:
            # Get the most recent weather data for this ward
            latest_data = WeatherData.objects.filter(ward=ward).order_by('-timestamp').first()
            
            if latest_data:
                # We have data! Get the inputs for our model.
                rainfall = latest_data.rainfall_mm
                river_level = latest_data.river_level_m
                
                # --- THE AI PART ---
                # Feed the data into our trained model
                risk_level = predict_flood_risk(rainfall, river_level)
                
                # Save the prediction to the Ward model
                ward.current_risk = risk_level
                ward.save()
                
                self.stdout.write(f"- {ward.name}: Data ({rainfall}mm, {river_level}m) -> Risk: {risk_level}")
                
            else:
                self.stdout.write(f"- {ward.name}: No weather data found. Skipping.")

        self.stdout.write(self.style.SUCCESS('Flood risk prediction complete.'))