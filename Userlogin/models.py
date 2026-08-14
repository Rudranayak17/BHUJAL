from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    # These are the choices for the dropdown
    class Roles(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        FARMER = 'FARMER', 'Farmer'
        RESEARCHER = 'RESEARCHER', 'Researcher'

    # Link to the existing User model
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # The role field
    role = models.CharField(
        max_length=20, 
        choices=Roles.choices, 
        default=Roles.FARMER
    )
    state = models.CharField(max_length=100, blank=True, default="")
    district = models.CharField(max_length=100, blank=True, default="")

    def __str__(self):
        return f"{self.user.username} - {self.role}"