import requests
import urllib.parse
from datetime import datetime, date, time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from django.utils import timezone
from django.db import close_old_connections
from Dashboard.models import Station, GroundwaterLevel, DistrictLog

INDIA_WRIS_URL = "https://indiawris.gov.in/Dataset/Ground Water Level"

def create_wris_session():
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session

def parse_iso_datetime(dt_str):
    """
    Parses ISO datetime string from India-WRIS and ensures timezone-aware datetime.
    """
    if not dt_str:
        return None
    try:
        dt = datetime.fromisoformat(dt_str)
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        return dt
    except (ValueError, TypeError):
        return None

def fetch_live_wris_data(state, district, start_date_str, end_date_str, station_name=None):
    """
    Fetches live data from India-WRIS API for a given state, district, and date range.
    Normalizes records, saves new Stations and GroundwaterLevels into DB cache,
    and returns count of fetched records.
    """
    session = create_wris_session()
    page = 0
    batch_size = 5000
    total_fetched = 0

    state_clean = state.strip()
    district_clean = district.strip()

    # Pre-cache existing stations for this state & district
    existing_stations = {
        s.station_name.lower(): s 
        for s in Station.objects.filter(state__iexact=state_clean, district__iexact=district_clean)
    }

    headers = {'accept': 'application/json'}

    while True:
        close_old_connections()
        state_q = urllib.parse.quote(state_clean)
        district_q = urllib.parse.quote(district_clean)

        url = (
            f"{INDIA_WRIS_URL}?"
            f"stateName={state_q}&districtName={district_q}"
            f"&agencyName=CGWB&startdate={start_date_str}&enddate={end_date_str}"
            f"&download=false&page={page}&size={batch_size}"
        )

        try:
            resp = session.post(url, headers=headers, timeout=30)
            if resp.status_code != 200:
                print(f"[WRIS Service] API return status {resp.status_code} for {state_clean}/{district_clean}")
                break

            payload = resp.json()
            data = payload.get("data", [])
            if not data:
                break

            total_fetched += len(data)

            # 1. Update DistrictLog
            DistrictLog.objects.get_or_create(state=state_clean, district=district_clean)

            # 2. Extract & Bulk Create Stations
            new_station_objs = []
            for item in data:
                s_name = item.get("stationName")
                s_state = item.get("state") or state_clean
                s_dist = item.get("district") or district_clean

                if not s_name:
                    continue

                # STRICT LOCATION INTEGRITY VALIDATION:
                # Reject items where returned state or district does not match requested location
                if s_state and s_state.strip().lower() != state_clean.lower():
                    continue
                if s_dist and s_dist.strip().lower() != district_clean.lower():
                    continue
                if station_name and station_name.strip().upper() != "ALL":
                    if s_name.strip().lower() != station_name.strip().lower():
                        continue

                s_name_key = s_name.strip().lower()
                if s_name_key not in existing_stations:
                    st_obj = Station(
                        station_code=item.get("stationCode"),
                        station_name=s_name.strip(),
                        state=state_clean,
                        district=district_clean,
                        latitude=item.get("latitude") if item.get("latitude") is not None else None,
                        longitude=item.get("longitude") if item.get("longitude") is not None else None,
                        aquifer_system=item.get("wellAquiferType")
                    )
                    new_station_objs.append(st_obj)
                    existing_stations[s_name_key] = st_obj

            if new_station_objs:
                Station.objects.bulk_create(new_station_objs, ignore_conflicts=True)
                # Re-fetch created stations to get Primary Keys
                refetched = Station.objects.filter(state__iexact=state_clean, district__iexact=district_clean)
                for s in refetched:
                    existing_stations[s.station_name.lower()] = s

            # 3. Prepare GroundwaterLevel records
            gw_records = []
            for item in data:
                s_name = item.get("stationName")
                raw_val = item.get("dataValue")
                raw_time = item.get("dataTime")
                s_state = item.get("state") or state_clean
                s_dist = item.get("district") or district_clean

                if not s_name or raw_val is None or raw_time is None:
                    continue

                # STRICT LOCATION INTEGRITY VALIDATION:
                if s_state and s_state.strip().lower() != state_clean.lower():
                    continue
                if s_dist and s_dist.strip().lower() != district_clean.lower():
                    continue
                if station_name and station_name.strip().upper() != "ALL":
                    if s_name.strip().lower() != station_name.strip().lower():
                        continue

                s_name_key = s_name.strip().lower()
                station_obj = existing_stations.get(s_name_key)
                if not station_obj or not station_obj.id:
                    continue

                dt = parse_iso_datetime(raw_time)
                if not dt:
                    continue

                try:
                    depth_val = float(raw_val)
                    gw_records.append(
                        GroundwaterLevel(
                            station=station_obj,
                            data_time=dt,
                            depth=depth_val
                        )
                    )
                except (ValueError, TypeError):
                    continue

            if gw_records:
                GroundwaterLevel.objects.bulk_create(gw_records, ignore_conflicts=True)

            if len(data) < batch_size:
                break

            page += 1

        except Exception as e:
            print(f"[WRIS Service] Network/parsing exception: {e}")
            break

    return total_fetched


def get_groundwater_data(state, district, start_date, end_date, station_name=None, force_live=False):
    """
    Primary API function to retrieve groundwater data.
    Checks DB cache first; if empty/incomplete or force_live, queries India-WRIS live.
    Returns (queryset, metadata_dict).
    """
    if isinstance(start_date, (datetime, date)):
        start_date_str = start_date.strftime("%Y-%m-%d")
    else:
        start_date_str = str(start_date)

    if isinstance(end_date, (datetime, date)):
        end_date_str = end_date.strftime("%Y-%m-%d")
    else:
        end_date_str = str(end_date)

    # Convert to datetimes for DB filtering
    s_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
    e_dt = datetime.strptime(end_date_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59)

    if timezone.is_naive(s_dt):
        s_dt = timezone.make_aware(s_dt, timezone.get_current_timezone())
    if timezone.is_naive(e_dt):
        e_dt = timezone.make_aware(e_dt, timezone.get_current_timezone())

    # Build DB filter
    base_filter = {
        "station__state__iexact": state.strip(),
        "station__district__iexact": district.strip(),
        "data_time__range": (s_dt, e_dt)
    }
    if station_name and station_name.strip() and station_name.strip().upper() != "ALL":
        base_filter["station__station_name__iexact"] = station_name.strip()

    records = GroundwaterLevel.objects.filter(**base_filter).select_related("station").order_by("data_time")

    source = "cache"
    # Check if cache hit is sufficient
    if force_live or not records.exists():
        # Live fetch from India-WRIS
        fetched = fetch_live_wris_data(state, district, start_date_str, end_date_str, station_name)
        source = "live"
        records = GroundwaterLevel.objects.filter(**base_filter).select_related("station").order_by("data_time")

    metadata = {
        "count": records.count(),
        "state": state,
        "district": district,
        "station": station_name or "ALL",
        "start_date": start_date_str,
        "end_date": end_date_str,
        "source": source
    }

    return records, metadata


def get_stations_for_location(state, district):
    """
    Returns list of Station objects (or dicts) for a given state & district.
    If none exist in DB, does a quick live fetch for date window to discover stations.
    """
    state_clean = state.strip()
    district_clean = district.strip()

    stations = Station.objects.filter(state__iexact=state_clean, district__iexact=district_clean).order_by("station_name")

    if not stations.exists():
        # Discovery fetch using 2025 to today
        end_str = datetime.now().strftime("%Y-%m-%d")
        start_str = "2025-01-01"
        fetch_live_wris_data(state_clean, district_clean, start_str, end_str)
        stations = Station.objects.filter(state__iexact=state_clean, district__iexact=district_clean).order_by("station_name")

    return list(stations.values("id", "station_name", "station_code", "latitude", "longitude", "aquifer_system"))
