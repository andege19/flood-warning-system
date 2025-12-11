"""
Fetches raw weather data from Open-Meteo API and saves to RawWeatherData table.
The Risk Engine (via Django Signal) will process this data separately.
"""
import requests
from django.core.management.base import BaseCommand
from core.models import Ward, RawWeatherData
from django.utils import timezone

class Command(BaseCommand):
    help = 'Fetches 24h rainfall forecast from Open-Meteo and stores raw data'

    WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("=== PHASE 1: INGESTOR ==="))
        self.stdout.write(self.style.NOTICE("Fetching weather data from Open-Meteo API..."))
        
        wards = Ward.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False
        )
        
        if not wards.exists():
            self.stdout.write(self.style.WARNING("No wards with coordinates found."))
            return

        success_count = 0
        error_count = 0

        for ward in wards:
            try:
                # Fetch from API
                params = {
                    'latitude': ward.latitude,
                    'longitude': ward.longitude,
                    'daily': 'rain_sum,relative_humidity_2m_max,temperature_2m_max',
                    'forecast_days': 1,
                    'timezone': 'auto'
                }

                response = requests.get(self.WEATHER_API_URL, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                forecasted_rain = data['daily']['rain_sum'][0]
                humidity = data['daily']['relative_humidity_2m_max'][0]
                temperature = data['daily']['temperature_2m_max'][0]
                
                if forecasted_rain is None:
                    self.stdout.write(
                        self.style.WARNING(f"  → No rain data for {ward.name}")
                    )
                    continue

                # Store raw data (Ingestor's only job)
                RawWeatherData.objects.create(
                    ward=ward,
                    rainfall_mm=forecasted_rain,
                    humidity_percent=humidity,
                    temperature_celsius=temperature,
                    # Risk Engine will fill in forecasted_risk_level via Signal
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ {ward.name}: {forecasted_rain}mm rain stored"
                    )
                )
                success_count += 1

            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f"  ✗ API Error for {ward.name}: {e}"))
                error_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ✗ Error for {ward.name}: {e}"))
                error_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\n=== INGESTOR COMPLETE ===\n"
                f"Success: {success_count} | Errors: {error_count}\n"
                f"Risk Engine will process this data via Django Signal..."
            )
        )