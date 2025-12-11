"""
Alternative Weather Data Service (Open-Meteo Extended)
Since NOAA only covers USA, we use Open-Meteo's advanced features
"""

import os
import requests
import logging
import json
from datetime import datetime, timezone as dt_timezone
from django.utils import timezone
from django.conf import settings
from core.models import Ward, WeatherDataLake

logger = logging.getLogger(__name__)

class NOAAService:
    """Alternative: Uses Open-Meteo's extended historical and climate data"""
    
    BASE_URL = "https://archive-api.open-meteo.com/v1/archive"
    ENABLED = True
    
    @staticmethod
    def is_enabled():
        """Check if service is enabled"""
        return NOAAService.ENABLED
    
    @staticmethod
    def fetch_ward_weather(ward):
        """Fetch historical/climate data for a ward"""
        try:
            coords = NOAAService._extract_coordinates(ward)
            if not coords:
                return None
            
            latitude, longitude = coords
            
            logger.info(f"Fetching NOAA (Historical) for {ward.name}: lat={latitude}, lon={longitude}")
            
            params = {
                'latitude': latitude,
                'longitude': longitude,
                'start_date': '2025-01-01',
                'end_date': '2025-11-19',
                'daily': 'precipitation_sum,temperature_2m_max,temperature_2m_min',
                'timezone': 'Africa/Nairobi'
            }
            
            response = requests.get(NOAAService.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"NOAA (Historical) data fetched for {ward.name}")
            
            return data
        
        except requests.exceptions.RequestException as e:
            logger.error(f"NOAA request error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error fetching NOAA data: {str(e)}")
            return None
    
    @staticmethod
    def store_weather_data(ward, data):
        """Store historical weather data"""
        try:
            daily = data.get('daily', {})
            times = daily.get('time', [])
            precipitation = daily.get('precipitation_sum', [])
            temp_max = daily.get('temperature_2m_max', [])
            temp_min = daily.get('temperature_2m_min', [])
            
            records_created = 0
            
            # Store last 30 days of historical data
            for i in range(min(30, len(times))):
                try:
                    # Parse ISO format date string
                    dt = datetime.fromisoformat(times[i])
                    # Add UTC timezone properly
                    timestamp = dt.replace(tzinfo=dt_timezone.utc)
                    
                    # Average min/max for temperature
                    temp_avg = None
                    if i < len(temp_max) and i < len(temp_min):
                        temp_avg = (temp_max[i] + temp_min[i]) / 2
                    
                    WeatherDataLake.objects.create(
                        ward=ward,
                        source='NOAA',
                        raw_data=data,
                        rainfall_mm=precipitation[i] if i < len(precipitation) else None,
                        temperature_celsius=temp_avg,
                        timestamp=timestamp
                    )
                    records_created += 1
                
                except Exception as e:
                    logger.error(f"Error storing NOAA record: {str(e)}")
                    continue
            
            logger.info(f"Stored {records_created} NOAA records for {ward.name}")
            return records_created
        
        except Exception as e:
            logger.error(f"Error storing NOAA data: {str(e)}")
            return 0
    
    @staticmethod
    def _extract_coordinates(ward):
        """Extract lat/lon from ward geometry"""
        try:
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
        if not NOAAService.is_enabled():
            logger.warning("NOAA not enabled")
            return 0
        
        wards = Ward.objects.all()
        success = 0
        
        for ward in wards:
            data = NOAAService.fetch_ward_weather(ward)
            if data:
                NOAAService.store_weather_data(ward, data)
                success += 1
        
        logger.info(f"NOAA: Fetched data for {success}/{wards.count()} wards")
        return success
