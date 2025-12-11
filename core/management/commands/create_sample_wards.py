import json
from django.core.management.base import BaseCommand
from core.models import Ward

class Command(BaseCommand):
    help = 'Create sample wards with GeoJSON polygons for Mathare and Mukuru'

    def handle(self, *args, **options):
        # GeoJSON polygon for Mathare (approximate coordinates around Nairobi)
        mathare_geojson = {
            "type": "Polygon",
            "coordinates": [[
                [36.80, -1.25],
                [36.82, -1.25],
                [36.82, -1.27],
                [36.80, -1.27],
                [36.80, -1.25]
            ]]
        }

        # GeoJSON polygon for Mukuru (approximate coordinates around Nairobi)
        mukuru_geojson = {
            "type": "Polygon",
            "coordinates": [[
                [36.78, -1.29],
                [36.80, -1.29],
                [36.80, -1.31],
                [36.78, -1.31],
                [36.78, -1.29]
            ]]
        }

        # Create or update Mathare
        mathare, created = Ward.objects.update_or_create(
            name='Mathare',
            defaults={
                'geojson': json.dumps(mathare_geojson),
                'current_risk_level': 'Low'
            }
        )
        status = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'{status} Ward: Mathare'))

        # Create or update Mukuru
        mukuru, created = Ward.objects.update_or_create(
            name='Mukuru',
            defaults={
                'geojson': json.dumps(mukuru_geojson),
                'current_risk_level': 'Low'
            }
        )
        status = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'{status} Ward: Mukuru'))

        self.stdout.write(self.style.SUCCESS('Sample wards created successfully.'))
