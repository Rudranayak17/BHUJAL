import json
import csv
from collections import defaultdict
from datetime import datetime, timedelta

from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
import plotly.graph_objs as go
from plotly.utils import PlotlyJSONEncoder

from .forms import GroundWaterForm
from .models import Station, GroundwaterLevel, DistrictLog
from Userlogin.models import Profile
from Dashboard.services.wris_service import get_groundwater_data, get_stations_for_location

def Dashboard(request):
    result = None
    plot_json = None
    
    form = GroundWaterForm()

    if request.method == 'POST':
        form = GroundWaterForm(request.POST)
        if form.is_valid():
            state = form.cleaned_data['stateName']
            district = form.cleaned_data['districtName']
            station = form.cleaned_data.get('stationName') or None
            start = form.cleaned_data['startDate']
            end = form.cleaned_data['endDate']

            records, metadata = get_groundwater_data(state, district, start, end, station_name=station)

            if records.exists():
                station_dict = defaultdict(list)
                for record in records:
                    s_name = record.station.station_name
                    dt_str = record.data_time.strftime('%Y-%m-%d %H:%M') if timezone.is_aware(record.data_time) else record.data_time.strftime('%Y-%m-%d %H:%M')
                    station_dict[s_name].append((dt_str, record.depth))

                traces = []
                for s_name, points in station_dict.items():
                    x_vals, y_vals = zip(*points)
                    traces.append(go.Scatter(
                        x=x_vals,
                        y=y_vals,
                        mode='lines+markers',
                        name=s_name,
                        connectgaps=True
                    ))

                loc_title = f"{district}, {state}" if not station or station.upper() == "ALL" else f"{station} ({district}, {state})"
                layout = go.Layout(
                    title=f"Groundwater Levels - {loc_title}",
                    xaxis=dict(title="Date"),
                    yaxis=dict(title="Depth (m bgl)"),
                    hovermode='closest',
                    template="plotly_white",
                    legend=dict(orientation="h", y=-0.2)
                )

                fig = go.Figure(data=traces, layout=layout)
                plot_json = json.dumps(fig, cls=PlotlyJSONEncoder)
                
                src_label = "Live India-WRIS API & Cached" if metadata["source"] == "live" else "Database Cache"
                result = {
                    "count": records.count(),
                    "msg": f"Loaded {records.count()} record(s) for {loc_title} (Source: {src_label})."
                }
            else:
                result = {
                    "error": f"No groundwater records were found for {district}, {state} between {start} and {end}."
                }

    return render(request, 'Dashboard.html', {
        'form': form,
        'result': result,
        'plot_json': plot_json
    })


def api_stations(request):
    """
    API endpoint returning JSON list of stations for selected State and District.
    """
    state = request.GET.get('state', '').strip()
    district = request.GET.get('district', '').strip()

    if not state or not district:
        return JsonResponse({'stations': []})

    stations = get_stations_for_location(state, district)
    return JsonResponse({'stations': stations})


@login_required
def FarmerDashboard(request):
    state = request.GET.get('state', '').strip()
    district = request.GET.get('district', '').strip()

    if not state or not district:
        first_log = DistrictLog.objects.first()
        if first_log:
            state = state or first_log.state
            district = district or first_log.district
        else:
            state = state or "Chhattisgarh"
            district = district or "Raipur"

    max_depth = 40.0 
    current_level = None 
    last_year_level = None
    
    status_class = 'caution'
    status_text = 'No Data'
    advice_text = "Select a station to view data."
    current_pct = 0
    last_year_pct = 0
    diff = 0
    trend_dir = "..."
    trend_icon = "horizontal_rule"
    trend_color = "var(--text-muted)"

    all_stations = Station.objects.filter(state__iexact=state, district__iexact=district).order_by("station_name")
    
    selected_id = request.GET.get('station_id')
    active_station = None

    if selected_id:
        active_station = all_stations.filter(id=selected_id).first()
    
    if not active_station and all_stations.exists():
        active_station = all_stations.first()

    if active_station:
        latest_record = GroundwaterLevel.objects.filter(station=active_station).order_by('-data_time').first()
        if not latest_record:
            end_str = datetime.now().strftime("%Y-%m-%d")
            start_str = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            get_groundwater_data(state, district, start_str, end_str)
            latest_record = GroundwaterLevel.objects.filter(station=active_station).order_by('-data_time').first()

        if latest_record:
            current_level = float(latest_record.depth)
            
            target_date = latest_record.data_time - timedelta(days=365)
            start_window = target_date - timedelta(days=15)
            end_window = target_date + timedelta(days=15)
            
            past_record = GroundwaterLevel.objects.filter(
                station=active_station,
                data_time__range=(start_window, end_window)
            ).order_by('-data_time').first()
            
            if past_record:
                last_year_level = float(past_record.depth)
            else:
                last_year_level = current_level 

    if current_level is not None:
        if current_level > -10:
            status_class = 'safe'
            status_text = 'Water Level Safe'
            advice_text = "Water levels are healthy. Standard irrigation permitted."
        elif -20 <= current_level <= -10:
            status_class = 'caution'
            status_text = 'Caution Required'
            advice_text = "Water levels are dropping. Limit pump usage to 4 hours."
        else:
            status_class = 'critical'
            status_text = 'Critical Drop'
            advice_text = "Emergency restriction. Use drip irrigation only."

        curr_water_col = max(0, max_depth - current_level)
        last_water_col = max(0, max_depth - last_year_level)

        current_pct = (curr_water_col / max_depth) * 100
        last_year_pct = (last_water_col / max_depth) * 100
        diff = current_level - last_year_level
        
        if diff > 0.1: 
            trend_dir = "risen"
            trend_icon = "trending_up"
            trend_color = "var(--success)"
        elif diff < -0.1:
            trend_dir = "dropped"
            trend_icon = "trending_down"
            trend_color = "var(--danger)"
        else:
            trend_dir = "remained stable"
            trend_icon = "remove"
            trend_color = "var(--text-muted)"

    context = {
        'state': state,
        'district': district,
        'stations': all_stations,
        'active_station': active_station,
        'user_district_name': f"{district} District, {state}",
        'current_level': current_level, 
        'last_year_level': last_year_level,
        'status_class': status_class,
        'status_text': status_text,
        'advice_text': advice_text,
        'current_pct': min(current_pct, 100),
        'last_year_pct': min(last_year_pct, 100),
        'diff': round(abs(diff), 2),
        'trend_dir': trend_dir,
        'trend_icon': trend_icon,
        'trend_color': trend_color,
    }
    return render(request, 'Farmer.html', context)

def Estimate(request):
    return render(request,'Estimate.html')

def Report(request):
    return render(request, 'Report.html')

@login_required(login_url='Login')
def export_groundwater_csv(request):
    if request.method == 'POST':
        state = request.POST.get('state')
        district = request.POST.get('district')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        if state and district and start_date and end_date:
            queryset, _ = get_groundwater_data(state, district, start_date, end_date)
        else:
            queryset = GroundwaterLevel.objects.select_related('station').all()
            if state:
                queryset = queryset.filter(station__state__iexact=state)
            if district:
                queryset = queryset.filter(station__district__iexact=district)
            if start_date:
                queryset = queryset.filter(data_time__gte=start_date)
            if end_date:
                queryset = queryset.filter(data_time__lte=end_date)

        response = HttpResponse(content_type='text/csv')
        filename = f"Groundwater_Report_{district if district else 'All'}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        writer.writerow(['Station Name', 'State', 'District', 'Date/Time', 'Depth (m)'])

        for entry in queryset:
            writer.writerow([
                entry.station.station_name,
                entry.station.state,
                entry.station.district,
                entry.data_time.strftime('%Y-%m-%d %H:%M'),
                entry.depth
            ])

        return response
    
    return Report(request)