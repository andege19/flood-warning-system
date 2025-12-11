"""
Open-Meteo Weather Service
Free weather API with no authentication required
"""

import requests
import logging
from datetime import datetime, timezone as dt_timezone
from django.utils import timezone
from core.models import Ward, WeatherDataLake

logger = logging.getLogger(__name__)

class OpenMeteoService:
    """Service for fetching weather data from Open-Meteo API"""
    
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    
    @staticmethod
    def fetch_ward_weather(ward):
        """
        Fetch weather data for a specific ward
        
        Args:
            ward (Ward): Ward object with latitude/longitude
        
        Returns:
            dict: Weather data or None if error
        """
        try:
            if not ward.geom_json:
                logger.warning(f"Ward {ward.name} has no geometry data")
                return None
            
            coords = OpenMeteoService._extract_coordinates(ward)
            if not coords:
                return None
            
            # coords are returned as (lat, lon) from _extract_coordinates
            latitude, longitude = coords
            
            # Kenya coordinates: latitude -4.67 to 4.62, longitude 28.33 to 41.90
            # Our data: lat should be negative (around -1), lon should be positive (around 36)
            logger.info(f"Fetching Open-Meteo for {ward.name}: lat={latitude}, lon={longitude}")
            
            params = {
                'latitude': latitude,
                'longitude': longitude,
                'hourly': 'rainfall,temperature_2m,humidity_2m,wind_speed_10m,cloud_cover',
                'daily': 'rainfall_sum,temperature_2m_max,temperature_2m_min',
                'timezone': 'Africa/Nairobi',
                'forecast_days': 7
            }
            
            response = requests.get(OpenMeteoService.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Open-Meteo data fetched for {ward.name}")
            
            return data
        
        except requests.exceptions.Timeout:
            logger.error(f"Open-Meteo timeout for {ward.name}")
            return None
        except Exception as e:
            logger.error(f"Error fetching Open-Meteo data for {ward.name}: {str(e)}")
            return None
    
    @staticmethod
    def store_weather_data(ward, data):
        """
        Store fetched weather data in database
        
        Args:
            ward (Ward): Ward object
            data (dict): Raw weather data from API
        
        Returns:
            int: Number of records stored
        """
        if not data or 'hourly' not in data:
            return 0
        
        try:
            hourly = data.get('hourly', {})
            times = hourly.get('time', [])
            rainfall = hourly.get('rainfall', [])
            temperature = hourly.get('temperature_2m', [])
            humidity = hourly.get('humidity_2m', [])
            wind_speed = hourly.get('wind_speed_10m', [])
            
            records_created = 0
            
            # Store last 24 hours of data
            for i in range(min(24, len(times))):
                try:
                    timestamp = datetime.fromisoformat(times[i]).replace(tzinfo=dt_timezone.utc)
                    
                    WeatherDataLake.objects.create(
                        ward=ward,
                        source='OPEN_METEO',
                        raw_data=data,
                        rainfall_mm=rainfall[i] if i < len(rainfall) else None,
                        temperature_celsius=temperature[i] if i < len(temperature) else None,
                        humidity_percent=humidity[i] if i < len(humidity) else None,
                        wind_speed_kmh=wind_speed[i] if i < len(wind_speed) else None,
                        timestamp=timestamp
                    )
                    records_created += 1
                
                except Exception as e:
                    logger.error(f"Error storing weather record: {str(e)}")
                    continue
            
            logger.info(f"Stored {records_created} Open-Meteo records for {ward.name}")
            return records_created
        
        except Exception as e:
            logger.error(f"Error storing weather data: {str(e)}")
            return 0
    
    @staticmethod
    def _extract_coordinates(ward):
        """
        Extract lat/lon from ward geometry
        
        GeoJSON format: [longitude, latitude]
        We need: (latitude, longitude) for Open-Meteo
        
        Our ward data has coordinates like: [36.771375, -1.307775]
        This means: longitude=36.771375 (correct for Kenya ~36-42)
                   latitude=-1.307775 (correct for Kenya ~-4 to +4)
        """
        try:
            import json
            geom = json.loads(ward.geom_json)
            
            if geom.get('type') == 'Polygon':
                coords = geom['coordinates'][0]
                
                # Extract all coordinates
                all_lons = [c[0] for c in coords]  # index 0 = longitude
                all_lats = [c[1] for c in coords]  # index 1 = latitude
                
                # Calculate center
                center_lon = sum(all_lons) / len(all_lons)
                center_lat = sum(all_lats) / len(all_lats)
                
                logger.info(f"Extracted coords from GeoJSON: lon={center_lon}, lat={center_lat}")
                
                # Return as (latitude, longitude) tuple for Open-Meteo
                return (center_lat, center_lon)
            
            return None
        except Exception as e:
            logger.error(f"Error extracting coordinates: {str(e)}")
            return None
    
    @staticmethod
    def fetch_all_wards():
        """Fetch weather for all wards"""
        wards = Ward.objects.all()
        success = 0
        
        for ward in wards:
            data = OpenMeteoService.fetch_ward_weather(ward)
            if data:
                OpenMeteoService.store_weather_data(ward, data)
                success += 1
        
        logger.info(f"Open-Meteo: Fetched data for {success}/{wards.count()} wards")
        return success
