#!/usr/bin/env python
"""
Complete database restoration script
Recreates schema and loads all initial data
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flood_warning_system.settings')
django.setup()

from django.core.management import call_command
from django.db import connection
from core.models import Ward, CustomUser
import json

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def main():
    print_section("DATABASE RESTORATION - COMPLETE PROCESS")
    
    # Step 1: Run migrations
    print_section("Step 1: Applying Migrations")
    try:
        call_command('migrate', verbosity=2)
        print("\n✓ Migrations applied successfully")
    except Exception as e:
        print(f"\n✗ Migration error: {e}")
        return False
    
    # Step 2: Create superuser
    print_section("Step 2: Creating Admin User")
    try:
        if not CustomUser.objects.filter(username='admin').exists():
            admin = CustomUser.objects.create_superuser(
                username='admin',
                email='admin@floodwarning.ke',
                password='Admin@123456',
                role='authority'
            )
            print(f"✓ Created admin user: {admin.username}")
        else:
            print("✓ Admin user already exists")
    except Exception as e:
        print(f"✗ Error creating admin: {e}")
    
    # Step 3: Load wards
    print_section("Step 3: Loading Nairobi Wards")
    try:
        call_command('load_initial_data')
        print(f"✓ Loaded {Ward.objects.count()} wards")
    except Exception as e:
        print(f"✗ Error loading wards: {e}")
    
    # Step 4: Load historical floods
    print_section("Step 4: Loading Historical Flood Data")
    try:
        call_command('import_historical_floods')
        print("✓ Historical flood data loaded")
    except Exception as e:
        print(f"✗ Error loading historical data: {e}")
    
    # Step 5: Ingest weather data
    print_section("Step 5: Ingesting Weather Data")
    try:
        call_command('ingest_weather_data')
        print("✓ Weather data ingested")
    except Exception as e:
        print(f"✗ Error ingesting weather: {e}")
    
    # Step 6: Train ML model
    print_section("Step 6: Training ML Model")
    try:
        call_command('train_advanced_model', force=True)
        print("✓ ML model trained")
    except Exception as e:
        print(f"✗ Error training model: {e}")
    
    # Step 7: System check
    print_section("Step 7: System Verification")
    try:
        call_command('check')
        print("✓ System check passed")
    except Exception as e:
        print(f"✗ System check failed: {e}")
        return False
    
    print_section("✓ DATABASE RESTORATION COMPLETE")
    print("\nNext steps:")
    print("1. Run: python manage.py runserver")
    print("2. Visit: http://localhost:8000")
    print("3. Login: admin / Admin@123456\n")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
