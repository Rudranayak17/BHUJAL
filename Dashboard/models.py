from django.db import models

class Station(models.Model):
    station_code = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    station_name = models.CharField(max_length=100) 
    state = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # --- NEW FIELDS FOR AQUIFER DATA ---
    aquifer_system = models.CharField(max_length=255, null=True, blank=True) 
    aquifer_details = models.TextField(null=True, blank=True) # Stores all extra info like Lithology/Age

    def __str__(self):
        return f"{self.station_name} ({self.district})"

    class Meta:
        unique_together = ('station_name', 'district', 'state')
        
class GroundwaterLevel(models.Model):
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    data_time = models.DateTimeField()
    depth = models.FloatField()

    class Meta:
        unique_together = ('station', 'data_time')

class DistrictLog(models.Model):
    state = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('state', 'district') 
        
    def __str__(self):
        return f"{self.district}, {self.state}"