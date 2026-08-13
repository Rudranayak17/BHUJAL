from django.shortcuts import render
from django.http import JsonResponse
from .models import Station

def station_search_view(request):
    """
    Renders the main page and provides the list of unique states
    for the initial dropdown.
    """
    states = Station.objects.values_list('state', flat=True).distinct().order_by('state')
    return render(request, 'station_search.html', {'states': states})

def load_districts(request):
    """
    AJAX: Returns a JSON list of districts for the selected state.
    """
    state_name = request.GET.get('state')
    
    if state_name:
        # Using __iexact for case-insensitive matching to be safe
        districts = Station.objects.filter(state__iexact=state_name)\
                                   .values_list('district', flat=True)\
                                   .distinct()\
                                   .order_by('district')
    else:
        districts = []
        
    return JsonResponse(list(districts), safe=False)

def load_stations(request):
    state_name = request.GET.get('state')
    district_name = request.GET.get('district')
    
    stations = Station.objects.filter(
        state__iexact=state_name, 
        district__iexact=district_name
    ).values(
        'station_name', 
        'station_code', 
        'latitude', 
        'longitude',
        'aquifer_yield',  # <--- Added
        'aquifer_area'    # <--- Added
    )
    
    return JsonResponse(list(stations), safe=False)

from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
from .models import Station, WaterReading
from datetime import datetime, timedelta

def storage_change_view(request):
    # 1. Load States for the dropdown
    states = Station.objects.values_list('state', flat=True).distinct().order_by('state')
    
    return render(request, 'storage_calculator.html', {'states': states})

from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone
from .models import Station, WaterReading
from datetime import datetime, timedelta

def calculate_storage(request):
    try:
        # --- 1. Get Parameters ---
        state = request.GET.get('state')
        district = request.GET.get('district')
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')

        if not all([state, district, start_date_str, end_date_str]):
            return JsonResponse({'error': 'Missing required parameters (state, district, dates).'}, status=400)

        # --- 2. Safe Date Parsing ---
        # We use standard datetime first
        start_dt = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date_str, '%Y-%m-%d')

        # Make Timezone Aware ONLY if your Django settings use timezones
        if settings.USE_TZ:
            start_dt = timezone.make_aware(start_dt)
            end_dt = timezone.make_aware(end_dt)

        # --- 3. Get Stations ---
        stations = Station.objects.filter(
            state__iexact=state, 
            district__iexact=district,
            aquifer_area__isnull=False,
            aquifer_yield__isnull=False
        )

        # Debug print to terminal
        print(f"DEBUG: Found {stations.count()} valid stations in {district}")

        results = []
        total_change_mcm = 0.0
        
        # Search window (Days)
        SEARCH_WINDOW = 45 

        for station in stations:
            # Find closest reading to Start Date
            start_reading = WaterReading.objects.filter(
                station=station, 
                timestamp__range=(
                    start_dt - timedelta(days=SEARCH_WINDOW), 
                    start_dt + timedelta(days=SEARCH_WINDOW)
                )
            ).order_by('timestamp').first() 

            # Find closest reading to End Date
            end_reading = WaterReading.objects.filter(
                station=station, 
                timestamp__range=(
                    end_dt - timedelta(days=SEARCH_WINDOW), 
                    end_dt + timedelta(days=SEARCH_WINDOW)
                )
            ).order_by('-timestamp').first()

            if start_reading and end_reading:
                # --- 4. Logic & Math ---
                
                # Determine Fluctuation based on value type
                # If values are large negative (Elevation), Change = End - Start
                if start_reading.value < 0:
                     fluctuation = end_reading.value - start_reading.value
                else:
                     # If values are positive (Depth Below Ground), Change = Start - End
                     fluctuation = start_reading.value - end_reading.value
                
                # Sy is percentage (e.g., 2.0 -> 0.02)
                # We perform a safe float conversion just in case
                sy_val = float(station.aquifer_yield)
                area_val = float(station.aquifer_area)
                
                sy = sy_val / 100.0
                
                # Change (m3) = Area (m2) * Sy * Fluctuation (m)
                change_m3 = area_val * sy * fluctuation
                
                # Convert to MCM
                change_mcm = change_m3 / 1_000_000.0
                total_change_mcm += change_mcm

                results.append({
                    'station': station.station_name,
                    'area': area_val,
                    'yield_percent': sy_val,
                    'start_depth': start_reading.value,
                    'end_depth': end_reading.value,
                    'start_date': start_reading.timestamp.strftime('%Y-%m-%d'),
                    'end_date': end_reading.timestamp.strftime('%Y-%m-%d'),
                    'fluctuation': round(fluctuation, 2),
                    'change_mcm': round(change_mcm, 6)
                })

        return JsonResponse({
            'district': district,
            'total_change_mcm': round(total_change_mcm, 6),
            'station_count': len(results),
            'data': results
        })

    except Exception as e:
        # --- CATCH CRASHES ---
        # This will print the error to the terminal AND send it to the browser
        print(f"🔥 CRITICAL ERROR IN VIEW: {str(e)}")
        import traceback
        traceback.print_exc() # Print full details to terminal
        return JsonResponse({'error': f"Server Error: {str(e)}"}, status=500)