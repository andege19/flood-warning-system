"""
OpenWeatherMap Weather Service
Free weather API with API key authentication
"""

import requests
import logging
from datetime import datetime
from django.utils import timezone
from django.conf import settings
import os

from core.models import Ward, WeatherDataLake

logger = logging.getLogger(__name__)

class OpenWeatherMapService:
    """Service for fetching weather data from OpenWeatherMap API"""
    
    BASE_URL = "https://api.openweathermap.org/data/2.5"
    API_KEY = os.getenv('OPENWEATHERMAP_API_KEY') or settings.ANYMAIL.get('OPENWEATHERMAP_API_KEY', '')
    
    @staticmethod
    def is_enabled():
        """Check if API key is configured"""
        key = OpenWeatherMapService.API_KEY
        if not key:
            logger.warning("OpenWeatherMap: No API key configured")
            return False
        logger.info(f"OpenWeatherMap enabled with key: {key[:10]}...")
        return True
    
    @staticmethod
    def fetch_ward_weather(ward):
        """Fetch current weather and forecast for a ward"""
        
        if not OpenWeatherMapService.is_enabled():
            logger.warning("OpenWeatherMap API key not configured")
            return None
        
        try:
            coords = OpenWeatherMapService._extract_coordinates(ward)
            if not coords:
                return None
            
            latitude, longitude = coords
            
            logger.info(f"Fetching OpenWeatherMap for {ward.name}: lat={latitude}, lon={longitude}")
            
            params = {
                'lat': latitude,
                'lon': longitude,
                'appid': OpenWeatherMapService.API_KEY,
                'units': 'metric'
            }
            
            response = requests.get(
                f"{OpenWeatherMapService.BASE_URL}/weather",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"OpenWeatherMap data fetched for {ward.name}")
            
            return data
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error("OpenWeatherMap: Invalid API key")
            else:
                logger.error(f"OpenWeatherMap HTTP error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching OpenWeatherMap data: {str(e)}")
            return None
    
    @staticmethod
    def store_weather_data(ward, data):
        """
        Store fetched weather data in database
        
        Args:
            ward (Ward): Ward object
            data (dict): Raw weather data from API
        
        Returns:
            bool: Success status
        """
        try:
            rain = 0
            if 'rain' in data:
                rain = data['rain'].get('1h', 0)
            
            WeatherDataLake.objects.create(
                ward=ward,
                source='OPENWEATHERMAP',
                raw_data=data,
                rainfall_mm=rain,
                temperature_celsius=data.get('main', {}).get('temp'),
                humidity_percent=data.get('main', {}).get('humidity'),
                wind_speed_kmh=data.get('wind', {}).get('speed', 0) * 3.6,  # m/s to km/h
                cloud_cover_percent=data.get('clouds', {}).get('all'),
                timestamp=timezone.now()
            )
            
            logger.info(f"Stored OpenWeatherMap record for {ward.name}")
            return True
        
        except Exception as e:
            logger.error(f"Error storing OpenWeatherMap data: {str(e)}")
            return False
    
    @staticmethod
    def _extract_coordinates(ward):
        """Extract lat/lon from ward geometry"""
        try:
            import json
            geom = json.loads(ward.geom_json)
            
            if geom.get('type') == 'Polygon':
                coords = geom['coordinates'][0]
                lats = [c[1] for c in coords]
                lons = [c[0] for c in coords]
                return (sum(lats) / len(lats), sum(lons) / len(lons))
            
            return None
        except Exception as e:
            logger.error(f"Error extracting coordinates: {str(e)}")
            return None
    
    @staticmethod
    def fetch_all_wards():
        """Fetch weather for all wards"""
        if not OpenWeatherMapService.is_enabled():
            logger.warning("OpenWeatherMap not enabled")
            return 0
        
        wards = Ward.objects.all()
        success = 0
        
        for ward in wards:
            data = OpenWeatherMapService.fetch_ward_weather(ward)
            if data:
                if OpenWeatherMapService.store_weather_data(ward, data):
                    success += 1
        
        logger.info(f"OpenWeatherMap: Fetched data for {success}/{wards.count()} wards")
        return success
