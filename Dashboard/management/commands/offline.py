import requests
import time
import urllib.parse
import threading
import concurrent.futures
from datetime import datetime,timedelta
from django.core.management.base import BaseCommand
from django.db import connection, close_old_connections
from Dashboard.models import Station, GroundwaterLevel

class Command(BaseCommand):
    help = "High-Performance Real-time fetcher: Runs parallel requests for the current date."

    def handle(self, *args, **options):
        # --- 1. AUTOMATIC DATE CONFIGURATION ---
        today = datetime.now()
        yesterday = today - timedelta(days=1)

        start_date = '2025-12-03'
        end_date = today.strftime("%Y-%m-%d")
        
        self.stdout.write(self.style.SUCCESS(f"--- AUTO-MODE: Fetching data for {today} ---"))

        # --- 2. THE DATA MAP ---
        DATA_MAP = {
            "Chhattisgarh": [
    "Balod",
    "Bastar",
    "Bemetara",
    "Bilaspur",
    "Dantewada",
    "Dhamtari",
    "Durg",
    "Gariaband",
    "Janjgir-Champa",
    "Jashpur",
    "Kabirdham",
    "Kanker",
    "Kondagaon",
    "Korba",
    "Mahasamund",
    "Mungeli",
    "Raigarh",
    "Raipur",
    "Rajnandgaon",
    "Sukma",
    "Surajpur",
    "Surguja"
  ],
  }

        # --- 3. OUTER LOOP: STATES (Sequential) ---
        # We keep states sequential to manage the Station Cache memory efficiently
        for state, districts in DATA_MAP.items():
            self.stdout.write(self.style.MIGRATE_HEADING(f"--- Processing State: {state} ---"))

            # Refresh Cache for the CURRENT State
            # We use a Lock to safely update this cache from multiple threads if needed
            print(f"Caching existing stations for {state}...")
            station_cache = {s.station_name: s for s in Station.objects.filter(state=state)}
            print(f"Loaded {len(station_cache)} stations into memory.")
            
            cache_lock = threading.Lock()

            # --- 4. PARALLEL PROCESSING: DISTRICTS ---
            # We launch a pool of workers (threads) to fetch districts simultaneously.
            # max_workers=10 is a safe number for most DBs (AWS RDS/Railway).
            # Too high (e.g., 50) might hit database connection limits.
            with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
                futures = []
                for district in districts:
                    futures.append(
                        executor.submit(
                            self.process_district, 
                            state, 
                            district, 
                            start_date, 
                            end_date, 
                            station_cache, 
                            cache_lock
                        )
                    )
                
                # Wait for all districts in this state to finish
                concurrent.futures.wait(futures)

        self.stdout.write(self.style.SUCCESS(f"Finished auto-fetch for {today}"))

    def process_district(self, state, district, start_date, end_date, station_cache, cache_lock):
        """
        Worker function that processes a single district.
        Running in a separate thread.
        """
        BATCH_SIZE = 5000
        headers = {'accept': 'application/json'}
        page = 0
        
        session = requests.Session()
        close_old_connections()

        while True:
            # ... (URL Construction Logic remains the same) ...
            state_q = urllib.parse.quote(state)
            district_q = urllib.parse.quote(district)

            url = (
                f"https://indiawris.gov.in/Dataset/Ground Water Level?"
                f"stateName={state_q}&districtName={district_q}"
                f"&agencyName=CGWB&startdate={start_date}&enddate={end_date}"
                f"&download=false&page={page}&size={BATCH_SIZE}"
            )

            try:
                net_start = time.time()
                response = session.post(url, headers=headers, timeout=20)
                net_time = time.time() - net_start
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"[{district}] Network error: {e}"))
                break

            if response.status_code != 200:
                self.stdout.write(self.style.WARNING(f"[{district}] API Error {response.status_code}"))
                break

            data = response.json().get("data", [])
            
            if not data:
                break 

            self.stdout.write(f"[{district}] Fetched {len(data)} records (Page {page}) in {net_time:.2f}s")

            # --- STEP 1: CREATE MISSING STATIONS WITH COORDS ---
            new_stations_to_create = []
            
            items_needing_check = [i for i in data if i.get('stationName')]
            
            with cache_lock:
                for item in items_needing_check: 
                    s_name = item.get('stationName')
                    
                    # Only create if it's NOT in our memory cache
                    if s_name and s_name not in station_cache:
                        
                        # --- MODIFICATION START: Extract Coords ---
                        # APIs sometimes return empty strings for missing data, convert to None
                        lat = item.get('latitude')
                        lon = item.get('longitude')
                        
                        # simple check to ensure we don't save empty strings
                        if lat == '': lat = None
                        if lon == '': lon = None
                        # ------------------------------------------

                        new_stations_to_create.append(
                            Station(
                                station_name=s_name, 
                                state=state, 
                                district=district,
                                latitude=lat,  # Added
                                longitude=lon  # Added
                            )
                        )
                        
                        # Placeholder in cache to prevent duplicates in this batch
                        station_cache[s_name] = None 

                if new_stations_to_create:
                    Station.objects.bulk_create(new_stations_to_create, ignore_conflicts=True)
                    
                    # Re-fetch to populate the cache with real objects (ids, etc)
                    created_names = [s.station_name for s in new_stations_to_create]
                    new_db_stations = Station.objects.filter(station_name__in=created_names, state=state)
                    for s in new_db_stations:
                        station_cache[s.station_name] = s
                    
                    print(f"  [{district}] -> Created {len(new_stations_to_create)} new stations with coords.")

            # --- STEP 2: PREPARE RECORDS (Unchanged) ---
            groundwater_records = []
            
            for item in data:
                s_name = item.get('stationName')
                try:
                    dt = datetime.fromisoformat(item.get('dataTime'))
                    depth = item.get('dataValue')
                    
                    station_obj = station_cache.get(s_name)

                    if station_obj:
                        groundwater_records.append(
                            GroundwaterLevel(
                                station=station_obj,
                                data_time=dt,
                                depth=depth
                            )
                        )
                except Exception:
                    continue

            # --- STEP 3: BULK INSERT (Unchanged) ---
            if groundwater_records:
                db_start = time.time()
                GroundwaterLevel.objects.bulk_create(groundwater_records, ignore_conflicts=True)
                db_time = time.time() - db_start
                self.stdout.write(self.style.SUCCESS(f"  [{district}] -> Saved {len(groundwater_records)} records in {db_time:.4f}s"))

            if len(data) < BATCH_SIZE:
                break
            page += 1