from django.urls import path
from . import views
urlpatterns = [
    path('', views.Dashboard, name='Dashboard'),
    path('Farmer/', views.FarmerDashboard, name='Farmer'),
    path('Researcher/', views.FarmerDashboard, name='Researcher'),
    path('Stakeholder/', views.FarmerDashboard, name='Stakeholder'),
    path('Estimate/', views.Estimate, name='Estimate'),
    path('Report/', views.Report, name='Report'),
    path('reports/export/', views.export_groundwater_csv, name='ExportCSV'),  # <--- The slash saves you!
    path('api/stations/', views.api_stations, name='api_stations'),
]