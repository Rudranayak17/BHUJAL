from django.core.management.base import BaseCommand
from Yeild.models import Station, WaterReading
from django.db import close_old_connections
import requests
import urllib.parse
import threading
import concurrent.futures
from datetime import datetime

class Command(BaseCommand):
    help = "Fetches groundwater level data and stores into DB"

    def handle(self, *args, **kwargs):
        self.fetch_groundwater()

    def fetch_groundwater(self):
        today = datetime.now()
        start_date = "2024-01-01"
        end_date = today.strftime("%Y-%m-%d")

        DATA_MAP = {
            "Chhattisgarh": [
                "Balod", "Bastar", "Bemetara", "Bilaspur", "Dantewada", 
                "Dhamtari", "Durg", "Gariaband", "Janjgir-Champa", "Jashpur",
                "Kabirdham", "Kanker", "Kondagaon", "Korba", "Mahasamund",
                "Mungeli", "Raigarh", "Raipur", "Rajnandgaon", "Sukma",
                "Surajpur", "Surguja"
            ]
        }

        for state, districts in DATA_MAP.items():
            print(f"Processing State => {state}")

            # Cache existing stations
            station_cache = {s.station_code: s for s in Station.objects.filter(state=state)}
            cache_lock = threading.Lock()

            with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
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

                concurrent.futures.wait(futures)

        print("✔ Data Fetch Completed")

    def process_district(self, state, district, start_date, end_date, station_cache, cache_lock):
        BATCH_SIZE = 5000
        page = 0
        session = requests.Session()

        while True:
            close_old_connections()

            state_q = urllib.parse.quote(state)
            district_q = urllib.parse.quote(district)

            url = (
                f"https://indiawris.gov.in/Dataset/Ground Water Level?"
                f"stateName={state_q}&districtName={district_q}"
                f"&agencyName=CGWB&startdate={start_date}&enddate={end_date}"
                f"&download=false&page={page}&size={BATCH_SIZE}"
            )

            try:
                response = session.post(url, headers={'accept': 'application/json'}, timeout=25)
            except Exception as e:
                print(f"[{district}] ❌ Network Failed: {e}")
                return

            if response.status_code != 200:
                print(f"[{district}] ❌ API Error: {response.status_code}")
                return

            data = response.json().get("data", [])
            if not data:
                return

            print(f"[{district}] Fetched {len(data)}")

            ### ---- CREATE STATIONS ---- ###
            new_stations = []
            with cache_lock:
                for item in data:
                    code = item.get("stationCode")
                    if code and code not in station_cache:

                        new_stations.append(
                            Station(
                                station_code=item.get("stationCode"),
                                station_name=item.get("stationName"),
                                latitude=item.get("latitude") or None,
                                longitude=item.get("longitude") or None,
                                well_depth=item.get("wellDepth") or None,
                                well_type=item.get("wellType"),
                                aquifer_type=item.get("wellAquiferType"),
                                state=item.get("state") or state,
                                district=item.get("district") or district
                            )
                        )

                        station_cache[code] = None

                if new_stations:
                    Station.objects.bulk_create(new_stations, ignore_conflicts=True)
                    created_codes = [s.station_code for s in new_stations]

                    for s in Station.objects.filter(station_code__in=created_codes):
                        station_cache[s.station_code] = s

                    print(f"[{district}] ➕ Stations Added: {len(new_stations)}")

            ### ---- CREATE WATER READINGS ---- ###
            readings = []
            for item in data:
                code = item.get("stationCode")
                station = station_cache.get(code)

                if not station:
                    continue

                try:
                    readings.append(
                        WaterReading(
                            station=station,
                            value=item.get("dataValue"),
                            timestamp=datetime.fromisoformat(item.get("dataTime")),
                            unit=item.get("unit") or "m"
                        )
                    )
                except:
                    continue

            if readings:
                WaterReading.objects.bulk_create(readings, ignore_conflicts=True)
                print(f"[{district}] 💾 Saved Readings: {len(readings)}")

            if len(data) < BATCH_SIZE:
                return

            page += 1
