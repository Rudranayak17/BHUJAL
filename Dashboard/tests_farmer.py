from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from Dashboard.models import GroundwaterLevel, Station
from Userlogin.models import Profile


class FarmerAuthRedirectTests(TestCase):
    def test_unauthenticated_farmer_redirects_to_app_login(self):
        response = self.client.get("/Dashboard/Farmer/", follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/Login", response["Location"])
        self.assertNotIn("/accounts/login", response["Location"])


class FarmerLocationFilterTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("locator", password="pass12345")
        Profile.objects.create(
            user=self.user,
            role="FARMER",
            state="Andhra Pradesh",
            district="Anantapur",
        )
        self.client.login(username="locator", password="pass12345")

    def test_haryana_query_does_not_fall_back_to_anantapur(self):
        response = self.client.get(
            "/Dashboard/Farmer/",
            {"state": "Haryana", "district": "Hisar"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hisar")
        self.assertContains(response, "Haryana")
        self.assertNotContains(response, "Hisar District, Andhra Pradesh")
        html = response.content.decode()
        self.assertIn('CURRENT_STATE = "Haryana"', html)
        self.assertIn('CURRENT_DISTRICT = "Hisar"', html)
        self.assertNotIn('CURRENT_STATE = "Andhra Pradesh"', html)


class FarmerDashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("farmer", password="pass12345")
        Profile.objects.create(
            user=self.user,
            role="FARMER",
            state="Andhra Pradesh",
            district="Anantapur",
        )
        self.client.login(username="farmer", password="pass12345")
        self.station = Station.objects.create(
            station_name="Tadipatri-pz_1",
            state="Andhra Pradesh",
            district="Anantapur",
            station_code="CGWBTEST",
            aquifer_system="Confined",
        )
        GroundwaterLevel.objects.create(
            station=self.station,
            data_time=timezone.now(),
            depth=-11.64,
        )

    @patch("Dashboard.views.get_stations_for_location", return_value=[])
    @patch("Dashboard.views.get_groundwater_data")
    def test_farmer_page_shows_wris_depth_and_station(self, mock_get, _mock_stations):
        mock_get.return_value = (
            GroundwaterLevel.objects.filter(station=self.station),
            {"source": "live"},
        )

        response = self.client.get(
            "/Dashboard/Farmer/",
            {"state": "Andhra Pradesh", "district": "Anantapur"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "11.6")
        self.assertContains(response, "Tadipatri-pz_1")
        self.assertContains(response, "India-WRIS")
        self.assertContains(response, "Caution Required")
        self.assertContains(response, "Andhra Pradesh")
        self.assertContains(response, "Anantapur")
        self.assertContains(response, "Chittoor")
        self.assertContains(response, "-- Select State --")
        self.assertContains(response, "-- Select District --")
        self.assertContains(response, "resultsSkeleton")
        self.assertContains(response, "Fetching groundwater data")
