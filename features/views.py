from django.shortcuts import render
from collections import defaultdict
from datetime import datetime
import requests
import pandas as pd
import numpy as np

def calculate_district_rainfall(rw_dict):
    """
    Calculates the average rainfall across the whole district 
    to use as a reference for all groundwater stations.
    """
    rw_records = []
    for station, values in rw_dict.items():
        for dt, val in values:
            if val is not None:
                # Handle the cumulative data issue (Bargi) vs Daily (Patan)
                # We tag them by station to group them first
                rw_records.append({'timestamp': dt, 'rainfall': float(val), 'station': station})
    
    if not rw_records:
        return None

    df_rain = pd.DataFrame(rw_records)
    df_rain['timestamp'] = pd.to_datetime(df_rain['timestamp'])

    # 1. Group by Station & Day (Average hourly data into one daily number)
    daily_per_station = df_rain.groupby(['station', pd.Grouper(key='timestamp', freq='D')])['rainfall'].mean().reset_index()
    
    # 2. Average all stations together for a "District Index"
    district_rain = daily_per_station.groupby('timestamp')['rainfall'].mean()
    
    return district_rain

def process_station_data(station_name, gw_values, district_rain_series):
    """
    Calculates recharge for a SINGLE station.
    """
    # 1. Prepare GW Data
    gw_records = [{'timestamp': dt, 'gwl': float(val)} for dt, val in gw_values if val is not None]
    
    if not gw_records:
        return []

    df_gw = pd.DataFrame(gw_records)
    df_gw['timestamp'] = pd.to_datetime(df_gw['timestamp'])
    
    # Average multiple readings per day for this specific station
    df_gw = df_gw.groupby('timestamp')['gwl'].mean()

    # 2. Merge with District Rain
    if district_rain_series is not None:
        df = pd.concat([df_gw, district_rain_series], axis=1)
    else:
        df = pd.DataFrame(df_gw)
        df['rainfall'] = 0.0

    # 3. Resample & Clean
    df.columns = ['gwl', 'rainfall'] # Ensure correct names
    df = df.resample('D').mean()
    df['gwl'] = df['gwl'].interpolate(method='linear')
    df['rainfall'] = df['rainfall'].fillna(0)

    # 4. Calculate Recharge (WTF Method)
    SY = 0.02
    df['water_change'] = df['gwl'].diff()
    df['recharge_est'] = df['water_change'].apply(lambda x: (x * SY) if x > 0 else 0)

    # 5. Format for JSON
    df = df.reset_index()
    df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d')
    df = df.fillna(0)
    
    return df[['timestamp', 'gwl', 'rainfall', 'recharge_est']].to_dict(orient='records')

def features(request):
    # SETTINGS
    state = 'Madhya Pradesh'
    district = 'Jabalpur'
    start = '2024-12-01'
    end = '2025-11-05'

    headers = {'accept': 'application/json'}
    GW_url = f"https://indiawris.gov.in/Dataset/Ground Water Level?stateName={state}&districtName={district}&agencyName=CGWB&startdate={start}&enddate={end}&download=false&page=0&size=10000"
    RW_url = f"https://indiawris.gov.in/Dataset/RainFall?stateName={state}&districtName={district}&agencyName=CWC&startdate={start}&enddate={end}&download=false&page=0&size=10000"

    gw_data = defaultdict(list)
    rw_data = defaultdict(list)
    error_message = None

    # FETCH DATA
    try:
        gw_resp = requests.post(GW_url, headers=headers, timeout=10)
        gw_resp.raise_for_status()
        for item in gw_resp.json().get('data', []):
            dt = datetime.fromisoformat(item['dataTime'])
            gw_data[item['stationName']].append((dt, item['dataValue']))
    except Exception as e:
        error_message = f"GW Error: {e}"

    try:
        rw_resp = requests.post(RW_url, headers=headers, timeout=10)
        rw_resp.raise_for_status()
        for item in rw_resp.json().get('data', []):
            dt = datetime.fromisoformat(item['dataTime'])
            rw_data[item['stationName']].append((dt, item['dataValue']))
    except Exception as e:
        pass # Rain errors shouldn't crash the app

    # PROCESS DATA
    stations_output = {} # Dict to hold data for each station {'StationA': [data], 'StationB': [data]}
    
    # 1. Get District Rain (One standard line for all charts)
    district_rain_series = calculate_district_rainfall(rw_data)

    # 2. Loop through every GW Station found
    total_district_recharge = 0
    
    if gw_data:
        for station_name, values in gw_data.items():
            station_clean_data = process_station_data(station_name, values, district_rain_series)
            if station_clean_data:
                stations_output[station_name] = station_clean_data
                
                # Sum up total recharge for this station
                station_total = sum(row['recharge_est'] for row in station_clean_data)
                total_district_recharge += station_total

    context = {
        'stations_data': stations_output, # MAIN DATA OBJECT
        'total_recharge': round(total_district_recharge, 4),
        'error_message': error_message
    }

    return render(request, 'feature.html', context)