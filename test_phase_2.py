"""
Phase 2 Testing Script
Run: python test_phase_2.py
"""

import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flood_warning_system.settings')
django.setup()

from core.models import Ward, WeatherDataLake
from core.services.data_pipeline import DataPipeline

def create_test_wards():
    """Create test wards"""
    print("\n" + "="*70)
    print("CREATING TEST WARDS")
    print("="*70)
    
    if Ward.objects.count() > 0:
        print("✓ Wards already exist")
        return
    
    wards_data = [
        {
            'name': 'Kibera',
            'coords': [[-1.3145, 36.7737], [-1.3089, 36.7783], [-1.3010, 36.7690], [-1.3067, 36.7645]]
        },
        {
            'name': 'Mathare',
            'coords': [[-1.2447, 36.8456], [-1.2380, 36.8520], [-1.2290, 36.8430], [-1.2357, 36.8365]]
        },
        {
            'name': 'Embakasi',
            'coords': [[-1.3189, 36.9010], [-1.3120, 36.9100], [-1.3000, 36.8980], [-1.3069, 36.8890]]
        },
        {
            'name': 'Kawangware',
            'coords': [[-1.3678, 36.7234], [-1.3600, 36.7320], [-1.3480, 36.7210], [-1.3558, 36.7124]]
        },
        {
            'name': 'Huruma',
            'coords': [[-1.2689, 36.8234], [-1.2620, 36.8310], [-1.2500, 36.8210], [-1.2569, 36.8134]]
        }
    ]
    
    for ward_data in wards_data:
        geom = {
            'type': 'Polygon',
            'coordinates': [ward_data['coords']]
        }
        
        ward = Ward.objects.create(
            name=ward_data['name'],
            geom_json=json.dumps(geom),
            current_risk_level='Low',
            population=50000
        )
        print(f"✓ Created ward: {ward.name}")
    
    print(f"\nTotal wards: {Ward.objects.count()}\n")


def run_data_ingestion():
    """Run data ingestion"""
    print("="*70)
    print("RUNNING DATA INGESTION")
    print("="*70 + "\n")
    
    result = DataPipeline.ingest_all_data()
    
    print(f"\n✓ Total Records: {result['total_records']}")
    print(f"✓ Timestamp: {result['timestamp']}")


def verify_data():
    """Verify ingested data"""
    print("\n" + "="*70)
    print("VERIFYING INGESTED DATA")
    print("="*70 + "\n")
    
    total = WeatherDataLake.objects.count()
    print(f"✓ Total weather records: {total}")
    
    for source in ['OPEN_METEO', 'OPENWEATHERMAP', 'NOAA']:
        count = WeatherDataLake.objects.filter(source=source).count()
        print(f"✓ {source}: {count} records")
    
    # Show latest record
    latest = WeatherDataLake.objects.order_by('-timestamp').first()
    if latest:
        print(f"\nLatest Record:")
        print(f"  Ward: {latest.ward.name}")
        print(f"  Source: {latest.source}")
        print(f"  Rainfall: {latest.rainfall_mm}mm")
        print(f"  Temperature: {latest.temperature_celsius}°C")
        print(f"  Humidity: {latest.humidity_percent}%")
        print(f"  Timestamp: {latest.timestamp}")
    
    print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    create_test_wards()
    run_data_ingestion()
    verify_data()
