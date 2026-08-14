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
from Dashboard.services.wris_service import (
    get_groundwater_data,
    get_stations_for_location,
    depth_below_ground,
)

FARMER_LOCATIONS = {
    "Andhra Pradesh": ["Anantapur", "Chittoor", "East Godavari"],
    "Chhattisgarh": ["Raipur", "Durg", "Bilaspur"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot"],
    "Karnataka": ["Bangalore Urban", "Mysuru", "Belagavi"],
    "Madhya Pradesh": ["Bhopal", "Indore", "Jabalpur", "Gwalior", "Sagar"],
    "Maharashtra": ["Pune", "Nagpur", "Nashik", "Aurangabad"],
    "Odisha": ["Baleshwar", "Khordha", "Cuttack"],
    "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai"],
    "Uttar Pradesh": ["Lucknow", "Varanasi", "Agra"],
}


def _downsample_series(points, limit=48):
    if len(points) <= limit:
        return points
    step = max(1, len(points) // limit)
    sampled = points[::step]
    if sampled[-1] != points[-1]:
        sampled.append(points[-1])
    return sampled[-limit:]

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
        profile = getattr(request.user, 'profile', None)
        if profile and getattr(profile, 'state', None) and getattr(profile, 'district', None):
            state = state or profile.state
            district = district or profile.district
        else:
            first_log = DistrictLog.objects.first()
            if first_log:
                state = state or first_log.state
                district = district or first_log.district
            else:
                state = state or "Andhra Pradesh"
                district = district or "Anantapur"

    locations = {name: list(dists) for name, dists in FARMER_LOCATIONS.items()}
    if state not in locations:
        locations[state] = [district] if district else []
    if district and district not in locations[state]:
        locations[state] = [district] + locations[state]

    max_depth = 25.0
    current_level = None
    last_year_level = None
    latest_time = None
    data_source = None
    series = []
    fetch_error = None

    status_class = 'caution'
    status_text = 'No Data'
    advice_text = "Choose a state and district to load India-WRIS station readings."
    current_pct = 0
    last_year_pct = 0
    diff = 0
    trend_dir = "..."
    trend_icon = "horizontal_rule"
    trend_color = "var(--text-muted)"

    try:
        get_stations_for_location(state, district)
    except Exception as exc:
        fetch_error = str(exc)

    all_stations = Station.objects.filter(
        state__iexact=state, district__iexact=district
    ).order_by("station_name")

    selected_id = request.GET.get('station_id')
    active_station = None
    if selected_id:
        active_station = all_stations.filter(id=selected_id).first()
    if not active_station and all_stations.exists():
        active_station = all_stations.first()

    if active_station:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=180)
        try:
            records, metadata = get_groundwater_data(
                state, district, start_date, end_date,
                station_name=active_station.station_name,
                max_pages=4,
            )
            data_source = metadata.get("source")
        except Exception as exc:
            fetch_error = str(exc)
            records = GroundwaterLevel.objects.none()
            metadata = {}

        latest_record = records.order_by('-data_time').first() if records is not None else None
        if latest_record:
            current_level = depth_below_ground(latest_record.depth)
            latest_time = latest_record.data_time

            target_date = latest_record.data_time - timedelta(days=365)
            past_record = records.filter(
                data_time__range=(target_date - timedelta(days=20), target_date + timedelta(days=20))
            ).order_by('-data_time').first()
            if past_record:
                last_year_level = depth_below_ground(past_record.depth)
            else:
                last_year_level = current_level

            raw_points = [
                {
                    "t": rec.data_time.strftime("%Y-%m-%d"),
                    "label": rec.data_time.strftime("%d %b"),
                    "d": round(depth_below_ground(rec.depth), 2),
                }
                for rec in records.order_by("data_time")
            ]
            # keep one reading per day (latest)
            by_day = {}
            for point in raw_points:
                by_day[point["t"]] = point
            series = _downsample_series(list(by_day.values()))

    if current_level is not None:
        if current_level < 8:
            status_class = 'safe'
            status_text = 'Water Level Safe'
            advice_text = "Groundwater is relatively shallow. Standard irrigation is fine."
        elif current_level < 15:
            status_class = 'caution'
            status_text = 'Caution Required'
            advice_text = "Water is deeper than usual. Limit pump use and prefer drip or evening watering."
        else:
            status_class = 'critical'
            status_text = 'Critical Drop'
            advice_text = "Water table is very deep. Use drip irrigation only and avoid long pumping."

        current_pct = max(4, min(100, ((max_depth - current_level) / max_depth) * 100))
        last_year_pct = max(4, min(100, ((max_depth - (last_year_level or current_level)) / max_depth) * 100))
        diff = round((last_year_level or current_level) - current_level, 2)

        if diff > 0.15:
            trend_dir = "risen"
            trend_icon = "trending_up"
            trend_color = "var(--success)"
        elif diff < -0.15:
            trend_dir = "dropped"
            trend_icon = "trending_down"
            trend_color = "var(--danger)"
        else:
            trend_dir = "remained stable"
            trend_icon = "remove"
            trend_color = "var(--text-muted)"

    chart_points = ""
    chart_min = None
    chart_max = None
    if series:
        depths = [p["d"] for p in series]
        chart_min = min(depths)
        chart_max = max(depths)
        span = max(chart_max - chart_min, 0.2)
        width = 320
        height = 90
        coords = []
        for idx, point in enumerate(series):
            x = 0 if len(series) == 1 else idx / (len(series) - 1) * width
            y = height - ((point["d"] - chart_min) / span) * (height - 8) - 4
            coords.append(f"{x:.1f},{y:.1f}")
        chart_points = " ".join(coords)

    context = {
        'state': state,
        'district': district,
        'locations': locations,
        'locations_json': json.dumps(locations),
        'stations': all_stations,
        'active_station': active_station,
        'user_district_name': f"{district} District, {state}",
        'current_level': current_level,
        'last_year_level': last_year_level,
        'latest_time': latest_time,
        'data_source': data_source,
        'fetch_error': fetch_error,
        'series': series,
        'chart_points': chart_points,
        'chart_min': chart_min,
        'chart_max': chart_max,
        'status_class': status_class,
        'status_text': status_text,
        'advice_text': advice_text,
        'current_pct': current_pct,
        'last_year_pct': last_year_pct,
        'diff': abs(diff),
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