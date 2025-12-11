import random
from django.core.management.base import BaseCommand
from core.models import Ward, WeatherData


from core.ml_model import predict_flood_risk

class Command(BaseCommand):
    help = 'Simulates fetching new weather data for all wards and runs predictions.'

    def handle(self, *args, **options):
        self.stdout.write("Starting data fetch and prediction simulation...")
        
        all_wards = Ward.objects.all()
        if not all_wards.exists():
            self.stdout.write(self.style.ERROR("No wards found. Please create wards in the admin panel."))
            return

        for ward in all_wards:
            # 1. SIMULATE FETCHING DATA
            # In a real app, this would be an API call, e.g.:
            # raw_data = requests.get(f"https://api.kmd.go.ke/data?ward={ward.name}")
            
            # For our simulation, we generate random data
            sim_rainfall = round(random.uniform(5.0, 100.0), 2)
            sim_river_level = round(random.uniform(1.0, 4.0), 2)
            
            # Save this "fetched" data to our log
            WeatherData.objects.create(
                ward=ward,
                rainfall_mm=sim_rainfall,
                river_level_m=sim_river_level
            )
            self.stdout.write(f"  > Fetched data for {ward.name}: {sim_rainfall}mm, {sim_river_level}m")

            # CALL THE AI BRAIN to get a prediction
            new_risk = predict_flood_risk(sim_rainfall, sim_river_level)
            
            # Only save if the risk level has changed
            if ward.current_risk_level != new_risk:
                ward.current_risk_level = new_risk
                ward.save() # <-- This .save() is what triggers our signal!
                
                self.stdout.write(self.style.SUCCESS(
                    f"  > AI Prediction for {ward.name}: {new_risk}. Risk level UPDATED."
                ))
            else:
                 self.stdout.write(self.style.WARNING(
                    f"  > AI Prediction for {ward.name}: {new_risk}. Risk level UNCHANGED."
                ))

        self.stdout.write(self.style.SUCCESS("Simulation complete."))