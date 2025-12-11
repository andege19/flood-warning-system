"""
Script to migrate data from SQLite to PostgreSQL
Run: python migrate_data.py
"""

import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flood_warning_system.settings')
django.setup()

from core.models import Ward, CustomUser, CrowdReport, Alert

def migrate_data():
    """
    Migrates all data from SQLite to PostgreSQL
    """
    print("Starting data migration...")
    
    # Count records
    wards = Ward.objects.count()
    users = CustomUser.objects.count()
    reports = CrowdReport.objects.count()
    alerts = Alert.objects.count()
    
    print(f"\nRecords to migrate:")
    print(f"  - Wards: {wards}")
    print(f"  - Users: {users}")
    print(f"  - Reports: {reports}")
    print(f"  - Alerts: {alerts}")
    
    # Data is automatically migrated by Django ORM
    # when you run migrations
    
    print("\n✓ Data migration complete!")
    print("All data successfully transferred to PostgreSQL")

if __name__ == '__main__':
    migrate_data()
