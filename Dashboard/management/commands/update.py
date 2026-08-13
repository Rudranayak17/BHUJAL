from django.core.management.base import BaseCommand
from Yeild.models import Station
from django.utils import timezone
import requests
import re
import concurrent.futures
import urllib3

# Suppress the "InsecureRequestWarning" so your terminal isn't flooded
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Command(BaseCommand):
    help = "Loops through all existing stations and updates Aquifer Area & Yield from IndiaWRIS API"

    def handle(self, *args, **kwargs):
        # Filter for stations that haven't been updated yet (optional, removes .all() to retry all)
        stations = list(Station.objects.all())
        total = len(stations)
        
        self.stdout.write(self.style.SUCCESS(f"🚀 Starting update for {total} stations..."))

        updated_count = 0
        failed_count = 0
        
        # We use a Session to keep headers persistent and speed up connections
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # ThreadPool to run 10 requests at once
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_station = {
                executor.submit(self.fetch_and_update, session, station): station 
                for station in stations
            }

            for i, future in enumerate(concurrent.futures.as_completed(future_to_station), 1):
                station = future_to_station[future]
                try:
                    success = future.result()
                    if success:
                        updated_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    failed_count += 1
                    self.stdout.write(self.style.ERROR(f"Error processing {station.station_code}: {e}"))

                # Progress Bar
                if i % 50 == 0:
                    self.stdout.write(f"Processed {i}/{total} | Updated: {updated_count} | No Data: {failed_count}")

        self.stdout.write(self.style.SUCCESS(f"\n✅ FINAL: Updated {updated_count} stations. (Failed/No Data: {failed_count})"))

    def fetch_and_update(self, session, station):
        if not station.latitude or not station.longitude:
            return False

        try:
            # URL: Geometry = Longitude, Latitude
            url = (
                f"https://arc.indiawris.gov.in/server/rest/services/SubInfoSysLCC/AquiferSystems/MapServer/2/query"
                f"?f=json&outFields=*&returnGeometry=false"
                f"&geometry={station.longitude},{station.latitude}"
                f"&geometryType=esriGeometryPoint&inSR=4326&spatialRel=esriSpatialRelIntersects&where=1=1"
            )

            # verify=False is CRITICAL here
            response = session.get(url, verify=False, timeout=15)
            
            if response.status_code != 200:
                return False
                
            data = response.json()

            if 'features' in data and len(data['features']) > 0:
                attrs = data['features'][0]['attributes']
                
                # --- Extract Area ---
                raw_area = attrs.get('area_re')
                if raw_area:
                    station.aquifer_area = float(raw_area)

                # --- Extract Yield ---
                raw_yield = attrs.get('yeild__') or attrs.get('Yield')
                if raw_yield:
                    # Regex extracts "8" from "8 - 16%" or "2.5" from "2.5 m/hr"
                    match = re.search(r"(\d+(\.\d+)?)", str(raw_yield))
                    if match:
                        station.aquifer_yield = float(match.group(1))

                station.last_api_update = timezone.now()
                station.save()
                return True
            
            return False 

        except Exception:
            return False