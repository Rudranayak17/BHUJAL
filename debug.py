import os
import django
from datetime import datetime, timedelta

# Setup Django (Required to run standalone)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DWLR.settings') # Ensure 'DWLR' is your project name
django.setup()

from Yeild.models import Station, WaterReading

def run_debug():
    # --- CONFIG ---
    STATION_NAME = "Cubbon Park_1"
    START_DATE = "2025-01-01" 
    END_DATE = "2025-02-01"
    # --------------

    print(f"\n--- DEBUGGING: {STATION_NAME} ---")

    try:
        station = Station.objects.get(station_name=STATION_NAME)
        print(f"✅ Station Found.")
        print(f"   Area: {station.aquifer_area}")
        print(f"   Yield: {station.aquifer_yield}")
    except Station.DoesNotExist:
        print(f"❌ Station '{STATION_NAME}' not found.")
        return

    # Check Total Readings
    count = WaterReading.objects.filter(station=station).count()
    print(f"📊 Total Water Readings in DB: {count}")

    if count == 0:
        print("⚠️  This station has NO water data. Fetcher script might have failed to save readings.")
        return

    # Check Date Range
    s_dt = datetime.strptime(START_DATE, "%Y-%m-%d")
    e_dt = datetime.strptime(END_DATE, "%Y-%m-%d")

    # Check Start Date Data
    r1 = WaterReading.objects.filter(
        station=station, 
        timestamp__range=(s_dt - timedelta(days=15), s_dt + timedelta(days=15))
    ).first()

    if r1:
        print(f"✅ Start Date Data Found: {r1.value}m ({r1.timestamp.date()})")
    else:
        print(f"❌ No data near {START_DATE}")

    # Check End Date Data
    r2 = WaterReading.objects.filter(
        station=station, 
        timestamp__range=(e_dt - timedelta(days=15), e_dt + timedelta(days=15))
    ).first()

    if r2:
        print(f"✅ End Date Data Found: {r2.value}m ({r2.timestamp.date()})")
    else:
        print(f"❌ No data near {END_DATE}")

    # Check latest available data
    last = WaterReading.objects.filter(station=station).order_by('-timestamp').first()
    if last:
        print(f"\nℹ️  Latest available reading is from: {last.timestamp.date()}")

# Run the function
if __name__ == "__main__":
    run_debug()