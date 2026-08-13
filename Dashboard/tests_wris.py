from django.test import TestCase, Client
from django.urls import reverse
from Dashboard.models import Station, GroundwaterLevel
from Dashboard.services.wris_service import get_groundwater_data, get_stations_for_location

class WRISIntegrationTests(TestCase):

    def test_01_wris_live_mp_jabalpur(self):
        records, meta = get_groundwater_data('Madhya Pradesh', 'Jabalpur', '2025-01-01', '2025-01-10')
        self.assertEqual(meta['state'], 'Madhya Pradesh')
        self.assertEqual(meta['district'], 'Jabalpur')
        self.assertGreater(records.count(), 0)
        for rec in records[:10]:
            self.assertEqual(rec.station.state.lower(), 'madhya pradesh')
            self.assertEqual(rec.station.district.lower(), 'jabalpur')

    def test_02_wris_live_chhattisgarh_raipur(self):
        records, meta = get_groundwater_data('Chhattisgarh', 'Raipur', '2025-01-01', '2025-01-10')
        self.assertEqual(meta['state'], 'Chhattisgarh')
        self.assertEqual(meta['district'], 'Raipur')
        self.assertGreater(records.count(), 0)
        for rec in records[:10]:
            self.assertEqual(rec.station.state.lower(), 'chhattisgarh')
            self.assertEqual(rec.station.district.lower(), 'raipur')

    def test_03_wris_live_maharashtra_pune(self):
        records, meta = get_groundwater_data('Maharashtra', 'Pune', '2025-01-01', '2025-01-10')
        self.assertEqual(meta['state'], 'Maharashtra')
        self.assertEqual(meta['district'], 'Pune')
        self.assertGreater(records.count(), 0)
        for rec in records[:10]:
            self.assertEqual(rec.station.state.lower(), 'maharashtra')
            self.assertEqual(rec.station.district.lower(), 'pune')

    def test_04_wris_live_rajasthan_jaipur(self):
        records, meta = get_groundwater_data('Rajasthan', 'Jaipur', '2025-01-01', '2025-01-10')
        self.assertEqual(meta['state'], 'Rajasthan')
        self.assertEqual(meta['district'], 'Jaipur')
        self.assertGreater(records.count(), 0)

    def test_05_cache_hit_versus_miss(self):
        # 1. First call -> Cache Miss -> LIVE fetch
        records_1, meta_1 = get_groundwater_data('Karnataka', 'Bangalore Urban', '2025-01-01', '2025-01-05')
        self.assertEqual(meta_1['source'], 'live')

        # 2. Second call -> Cache Hit -> DB retrieval
        records_2, meta_2 = get_groundwater_data('Karnataka', 'Bangalore Urban', '2025-01-01', '2025-01-05')
        self.assertEqual(meta_2['source'], 'cache')
        self.assertEqual(records_1.count(), records_2.count())

    def test_06_multiple_date_ranges(self):
        # Jan 2025
        r_jan, m_jan = get_groundwater_data('Madhya Pradesh', 'Jabalpur', '2025-01-01', '2025-01-31')
        self.assertGreater(r_jan.count(), 0)

        # Jun 2025
        r_jun, m_jun = get_groundwater_data('Madhya Pradesh', 'Jabalpur', '2025-06-01', '2025-06-30')
        self.assertGreater(r_jun.count(), 0)

        # Dec 2025
        r_dec, m_dec = get_groundwater_data('Madhya Pradesh', 'Jabalpur', '2025-12-01', '2025-12-31')
        self.assertGreater(r_dec.count(), 0)

    def test_07_invalid_location_handling(self):
        records, meta = get_groundwater_data('NonExistentState', 'InvalidDistrict', '2025-01-01', '2025-01-05')
        self.assertEqual(records.count(), 0)

    def test_08_api_stations_endpoint(self):
        client = Client()
        response = client.get(reverse('api_stations'), {'state': 'Madhya Pradesh', 'district': 'Jabalpur'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('stations', data)
        self.assertGreater(len(data['stations']), 0)

    def test_09_dashboard_post_request_and_graph(self):
        client = Client()
        response = client.post(reverse('Dashboard'), {
            'stateName': 'Maharashtra',
            'districtName': 'Pune',
            'stationName': 'ALL',
            'startDate': '2025-01-01',
            'endDate': '2025-01-10'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('plot_json', response.context)
        self.assertIsNotNone(response.context['plot_json'])
        self.assertIn('Pune', response.context['plot_json'])
