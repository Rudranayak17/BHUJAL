import requests
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.core.management.base import BaseCommand
from django.db.models import Q
from Dashboard.models import Station

class Command(BaseCommand):
    help = "Enrich existing stations with Aquifer data using stored coordinates."

    def add_arguments(self, parser):
        # Allow user to filter by state or district if they want
        parser.add_argument('--state', type=str, help='Filter by State name')
        parser.add_argument('--district', type=str, help='Filter by District name')

    def handle(self, *args, **options):
        target_state = options['state']
        target_district = options['district']

        self.stdout.write(self.style.MIGRATE_HEADING("--- Starting Aquifer Enrichment ---"))

        # 1. FILTER STATIONS
        # We need stations that HAVE coords (latitude is not Null)
        # AND DO NOT HAVE aquifer info (aquifer_system is Null or Empty)
        stations = Station.objects.filter(
            latitude__isnull=False, 
            longitude__isnull=False
        ).filter(
            Q(aquifer_system__isnull=True) | Q(aquifer_system__exact='')
        )

        if target_state:
            stations = stations.filter(state__iexact=target_state)
        if target_district:
            stations = stations.filter(district__iexact=target_district)

        total_count = stations.count()
        
        if total_count == 0:
            self.stdout.write(self.style.WARNING("No stations found needing update (or missing coords)."))
            return

        self.stdout.write(f"Found {total_count} stations to process.")

        # 2. PARALLEL PROCESSING
        # We use threads to make this fast (network bound)
        max_workers = 10 
        success_count = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Create a dictionary to map futures to stations
            future_to_station = {
                executor.submit(self.fetch_aquifer_data, station): station 
                for station in stations
            }

            for future in as_completed(future_to_station):
                station = future_to_station[future]
                try:
                    result = future.result()
                    if result:
                        success_count += 1
                        if success_count % 50 == 0:
                            self.stdout.write(f"Progress: {success_count}/{total_count} updated...")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error processing {station.station_name}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"--- Finished! Updated {success_count} stations. ---"))

    def fetch_aquifer_data(self, station):
        """
        Performs the API request for a single station.
        """
        # ArcGIS expects 'Longitude,Latitude'
        geo_coords = f"{station.longitude},{station.latitude}"
        
        url = (
            "https://arc.indiawris.gov.in/server/rest/services/SubInfoSysLCC/AquiferSystems/MapServer/2/query?"
            "f=json"
            "&outFields=*"
            "&returnGeometry=false"
            "&geometryType=esriGeometryPoint"
            "&inSR=4326"
            "&spatialRel=esriSpatialRelIntersects"
            f"&geometry={geo_coords}"
        )

        try:
            # 10s timeout to prevent hanging threads
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                features = data.get('features', [])
                
                if features:
                    attrs = features[0].get('attributes', {})
                    
                    # Try to find the Aquifer Name in common keys
                    # 'Aquifer_Sy' and 'P_Aquifer' are common field names in WRIS
                    aq_name = attrs.get('Aquifer_Sy') or attrs.get('Aquifer_System') or attrs.get('P_Aquifer')
                    
                    if aq_name:
                        station.aquifer_system = aq_name
                        # Save full attributes as string just in case you need other data later
                        station.aquifer_details = json.dumps(attrs) 
                        station.save()
                        return True
                    else:
                        # Found location, but data fields were empty
                        station.aquifer_system = "Unknown"
                        station.save()
                        return True
                else:
                    # No aquifer polygon found at this location
                    station.aquifer_system = "Not Mapped"
                    station.save()
                    return True
            
        except Exception:
            # Silently fail for network glitches, will retry next run
            return False
        
        return False