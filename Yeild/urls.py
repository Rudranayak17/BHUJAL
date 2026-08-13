from django.urls import path
from . import views
urlpatterns = [
    path('station-search/', views.station_search_view, name='station_search'),
    path('ajax/load-districts/', views.load_districts, name='ajax_load_districts'),
    path('ajax/load-stations/', views.load_stations, name='ajax_load_stations'),
    path('storage-calculator/', views.storage_change_view, name='storage_calculator'),
    path('api/calculate-storage/', views.calculate_storage, name='api_calculate_storage'),  
]
