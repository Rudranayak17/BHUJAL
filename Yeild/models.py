from django.db import models

class Station(models.Model):
    station_code = models.CharField(max_length=50, unique=True)
    station_name = models.CharField(max_length=150)
    latitude = models.FloatField()
    longitude = models.FloatField()
    well_depth = models.FloatField()
    well_type = models.CharField(max_length=50, null=True, blank=True)
    aquifer_type = models.CharField(max_length=50, null=True, blank=True)
    state = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
# --- NEW FIELDS FOR API DATA ---
    aquifer_yield = models.FloatField(null=True, blank=True, help_text="Extracted numeric yield (e.g., 2.0)")
    aquifer_area = models.FloatField(null=True, blank=True, help_text="Area from area_re field")
    
    # Optional: Timestamp to know when we last updated it
    last_api_update = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.station_name} ({self.station_code})"


class WaterReading(models.Model):
    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name="readings")
    value = models.FloatField()                  # water level
    timestamp = models.DateTimeField()           # dataTime from API
    unit = models.CharField(max_length=20, default="m")

    class Meta:
        ordering = ['-timestamp']                # newest first
        unique_together = ("station", "timestamp")  # prevent duplicates

    def __str__(self):
        return f"{self.station.station_name} - {self.timestamp}"

class Aquifer(models.Model):
    # Mapping 'S.No' to serial_number
    serial_number = models.FloatField(help_text="Original serial number from the CSV") 
    
    principal = models.CharField(max_length=100, help_text="Principal Aquifer System (e.g., Alluvium)")
    code = models.CharField(max_length=50, help_text="Aquifer Code (e.g., AL01)")
    name = models.CharField(max_length=255, help_text="Specific description or rock type")
    age = models.CharField(max_length=100, help_text="Geological Age")
    
    # Numeric fields
    recommended = models.FloatField(help_text="Recommended value")
    minimum = models.FloatField(help_text="Minimum value")
    maximum = models.FloatField(help_text="Maximum value")

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        ordering = ['serial_number']
        verbose_name = "Aquifer Data"
        verbose_name_plural = "Aquifer Data"