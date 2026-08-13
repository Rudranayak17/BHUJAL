from django import forms

class GroundWaterForm(forms.Form):
    stateName = forms.CharField(label="State Name", max_length=100)
    districtName = forms.CharField(label="District Name", max_length=100)
    stationName = forms.CharField(label="Station Name", max_length=150, required=False)
    startDate = forms.DateField(label="Start Date", widget=forms.DateInput(attrs={'type': 'date'}))
    endDate = forms.DateField(label="End Date", widget=forms.DateInput(attrs={'type': 'date'}))
