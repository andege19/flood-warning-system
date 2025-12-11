"""
Unified Data Pipeline
Combines all weather data sources with fallback logic
"""

import logging
from core.services.openweathermap_service import OpenWeatherMapService
from core.services.noaa_service import NOAAService
from core.models import Ward

logger = logging.getLogger(__name__)

class DataPipeline:
    """Unified data ingestion pipeline"""
    
    # Disabled Open-Meteo due to coordinate validation issues
    # Using OpenWeatherMap + NOAA instead (more reliable)
    SOURCES = [
        ('OpenWeatherMap', OpenWeatherMapService),
        ('NOAA', NOAAService),
    ]
    
    @staticmethod
    def ingest_all_data():
        """
        Run complete data ingestion pipeline
        Tries all sources, uses fallback if one fails
        
        Returns:
            dict: Ingestion results
        """
        logger.info("=" * 70)
        logger.info("Starting Data Ingestion Pipeline")
        logger.info("=" * 70)
        
        results = {
            'timestamp': None,
            'sources': {},
            'total_wards': 0,
            'total_records': 0,
            'success': False
        }
        
        # Get timestamp
        from django.utils import timezone
        results['timestamp'] = timezone.now().isoformat()
        
        # Get ward count
        results['total_wards'] = Ward.objects.count()
        
        # Run each source
        for source_name, source_class in DataPipeline.SOURCES:
            try:
                logger.info(f"\nRunning {source_name} ingestion...")
                count = source_class.fetch_all_wards()
                results['sources'][source_name] = {
                    'success': True,
                    'records': count
                }
                results['total_records'] += count
                logger.info(f"{source_name}: Success ({count} records)")
            
            except Exception as e:
                logger.error(f"{source_name}: Failed - {str(e)}")
                results['sources'][source_name] = {
                    'success': False,
                    'error': str(e)
                }
        
        # Determine overall success (at least one source succeeded)
        success_count = sum(1 for s in results['sources'].values() if s.get('success'))
        results['success'] = success_count > 0
        
        logger.info("\n" + "=" * 70)
        logger.info("Data Ingestion Pipeline Complete")
        logger.info(f"Total Records Stored: {results['total_records']}")
        logger.info(f"Sources Successful: {success_count}/{len(DataPipeline.SOURCES)}")
        logger.info("=" * 70 + "\n")
        
        return results
    
    @staticmethod
    def get_latest_data_status():
        """Get status of latest data ingestion"""
        from core.models import WeatherDataLake
        
        latest = WeatherDataLake.objects.order_by('-ingested_at').first()
        
        if not latest:
            return {
                'status': 'No data',
                'last_update': None,
                'records': 0
            }
        
        total_records = WeatherDataLake.objects.count()
        
        return {
            'status': 'Current',
            'last_update': latest.ingested_at.isoformat(),
            'records': total_records,
            'sources': list(
                WeatherDataLake.objects.values('source').distinct()
            )
        }
    
    @staticmethod
    def backfill_historical_data(days=7):
        """
        Backfill historical data from multiple sources
        
        Args:
            days (int): Days of history to fetch
        
        Returns:
            dict: Backfill results
        """
        logger.info(f"Starting historical data backfill for {days} days...")
        
        results = {
            'days_backfilled': days,
            'total_records': 0,
            'sources': {}
        }
        
        # For now, just fetch current data multiple times
        for day in range(days):
            logger.info(f"Backfilling day {day+1}/{days}...")
            result = DataPipeline.ingest_all_data()
            results['total_records'] += result['total_records']
        
        logger.info(f"Backfill complete: {results['total_records']} records stored")
        return results
