from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from Dashboard.services.wris_service import fetch_live_wris_data

class Command(BaseCommand):
    help = "Controlled bulk ingestion tool for India-WRIS groundwater data."

    def add_arguments(self, parser):
        parser.add_argument('--state', type=str, help='State name (e.g. "Madhya Pradesh")')
        parser.add_argument('--district', type=str, help='District name (e.g. "Jabalpur")')
        parser.add_argument('--station', type=str, help='Station name (optional)')
        parser.add_argument('--start-date', type=str, help='Start date YYYY-MM-DD (defaults to 1 year ago)')
        parser.add_argument('--end-date', type=str, help='End date YYYY-MM-DD (defaults to today)')

    def handle(self, *args, **options):
        state = options.get('state')
        district = options.get('district')
        station = options.get('station')
        start_date = options.get('start_date')
        end_date = options.get('end_date')

        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

        if not state or not district:
            self.stdout.write(self.style.ERROR('Please specify both --state and --district.'))
            self.stdout.write('Example: python manage.py fetch_wris_data --state "Madhya Pradesh" --district "Jabalpur" --start-date 2025-01-01 --end-date 2025-12-31')
            return

        self.stdout.write(self.style.SUCCESS(f'Fetching India-WRIS data for {district}, {state} ({start_date} to {end_date})...'))

        count = fetch_live_wris_data(state, district, start_date, end_date, station_name=station)
        self.stdout.write(self.style.SUCCESS(f'[OK] Ingestion complete! Saved/updated {count} record(s) in local DB cache.'))
