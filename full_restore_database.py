#!/usr/bin/env python
"""
Complete database restoration script
Recreates all data from scratch
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flood_warning_system.settings')
django.setup()

from django.core.management import call_command
from core.models import Ward, CustomUser, WeatherDataLake, FloodPrediction, HistoricalFloodEvent
from django.db import connection

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def check_database_connection():
    """Check if database connection works"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def main():
    print_section("COMPLETE DATABASE RESTORATION")
    
    # Check connection
    if not check_database_connection():
        print("✗ Cannot connect to database. Check your .env file:")
        print("  DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD")
        return False
    
    print("✓ Database connection successful")
    
    # Step 1: Run migrations
    print_section("Step 1: Running Migrations")
    try:
        call_command('migrate', verbosity=1)
        print("✓ All migrations applied")
    except Exception as e:
        print(f"✗ Migration error: {e}")
        return False
    
    # Step 2: Create admin user
    print_section("Step 2: Creating Admin User")
    try:
        if CustomUser.objects.filter(username='admin').exists():
            print("✓ Admin user already exists")
            admin = CustomUser.objects.get(username='admin')
        else:
            admin = CustomUser.objects.create_superuser(
                username='admin',
                email='admin@floodwarning.ke',
                password='Admin@123456',
                role='authority'
            )
            print(f"✓ Created admin user: {admin.username}")
    except Exception as e:
        print(f"✗ Error creating admin: {e}")
        return False
    
    # Step 3: Load wards
    print_section("Step 3: Loading Nairobi Wards (32 wards)")
    try:
        call_command('load_initial_data', force=True, verbosity=1)
        ward_count = Ward.objects.count()
        print(f"✓ Loaded {ward_count} wards")
    except Exception as e:
        print(f"✗ Error loading wards: {e}")
        return False
    
    # Step 4: Load historical floods (with --force to prevent duplicates)
    print_section("Step 4: Loading Historical Flood Data (2015-2025)")
    try:
        call_command('import_historical_floods', force=True, verbosity=1)
        event_count = HistoricalFloodEvent.objects.count()
        print(f"✓ Loaded {event_count} historical flood events")
    except Exception as e:
        print(f"⚠ Warning: {e}")
    
    # Step 4.5: Clean any duplicates
    print_section("Step 4.5: Cleaning Duplicate Data")
    try:
        call_command('clean_duplicates', verbosity=1)
        print("✓ Duplicates cleaned")
    except Exception as e:
        print(f"⚠ Warning: {e}")
    
    # Step 5: Ingest weather data
    print_section("Step 5: Ingesting Weather Data")
    try:
        result = call_command('ingest_weather_data', verbosity=1)
        weather_count = WeatherDataLake.objects.count()
        print(f"✓ Ingested weather data ({weather_count} records total)")
    except Exception as e:
        print(f"⚠ Warning: {e}")
        # Don't fail on this
    
    # Step 6: Train ML model
    print_section("Step 6: Training ML Model")
    try:
        call_command('train_advanced_model', force=True, verbosity=1)
        print("✓ ML model trained successfully")
    except Exception as e:
        print(f"⚠ Warning: {e}")
        # Don't fail on this
    
    # Step 7: System check
    print_section("Step 7: System Verification")
    try:
        call_command('check', verbosity=0)
        print("✓ System check passed")
    except Exception as e:
        print(f"✗ System check failed: {e}")
        return False
    
    # Summary
    print_section("DATABASE STATISTICS")
    
    users = CustomUser.objects.count()
    wards = Ward.objects.count()
    weather = WeatherDataLake.objects.count()
    predictions = FloodPrediction.objects.count()
    events = HistoricalFloodEvent.objects.count()
    
    print(f"Users:           {users}")
    print(f"Wards:           {wards}")
    print(f"Weather Records: {weather}")
    print(f"Predictions:     {predictions}")
    print(f"Historical Events: {events}")
    
    print_section("✓ RESTORATION COMPLETE")
    
    print("\n📝 NEXT STEPS:")
    print("\n1. Start the server:")
    print("   python manage.py runserver\n")
    print("2. Visit in browser:")
    print("   http://localhost:8000\n")
    print("3. Login credentials:")
    print("   Username: admin")
    print("   Password: Admin@123456\n")
    print("4. Access main pages:")
    print("   Map:      http://localhost:8000/map/")
    print("   Flood Info: http://localhost:8000/flood-information/")
    print("   Admin:    http://localhost:8000/authority/dashboard/\n")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
