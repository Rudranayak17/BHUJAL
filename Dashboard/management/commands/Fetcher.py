from django.core.management.base import BaseCommand
from Yeild.models import Station, WaterReading
from django.db import close_old_connections
import requests
import urllib.parse
import threading
import concurrent.futures
from datetime import datetime

class Command(BaseCommand):
    help = "Fetches groundwater level data and stores into DB"

    def handle(self, *args, **kwargs):
        self.fetch_groundwater()

    def fetch_groundwater(self):
        today = datetime.now()
        start_date = "2025-06-08"
        end_date = today.strftime("%Y-%m-%d")

        DATA_MAP = {
  "Andhra Pradesh": [
    "Alluri Sitharama Raju",
    "Ananthapuramu",
    "Annamayya",
    "Bapatla",
    "Chittoor",
    "East Godavari",
    "Eluru",
    "Guntur",
    "Krishna",
    "Kurnool",
    "Nandyal",
    "Nellore",
    "Palnadu",
    "Prakasam",
    "Srikakulam",
    "Sri Sathya Sai",
    "Visakhapatnam",
    "Vizianagaram",
    "West Godavari"
  ],
  "Arunachal Pradesh": [
    "Changlang",
    "East Siang",
    "Lohit",
    "Lower Dibang Valley",
    "Lower Subansiri",
    "Namsai",
    "Papum Pare",
    "Tirap"
  ],
  "Assam": [
    "Baksa",
    "Barpeta",
    "Biswanath",
    "Bongaigaon",
    "Cachar",
    "Chirang",
    "Darrang",
    "Dhemaji",
    "Dhubri",
    "Dibrugarh",
    "Goalpara",
    "Golaghat",
    "Hailakandi",
    "Hojai",
    "Jorhat",
    "Kamrup",
    "Kamrup Metropolitan",
    "Karbi Anglong",
    "Karimganj",
    "Kokrajhar",
    "Lakhimpur",
    "Nagaon",
    "Nalbari",
    "Sonitpur",
    "Tinsukia",
    "Udalguri"
  ],
  "Bihar": [
    "Araria",
    "Aurangabad",
    "Banka",
    "Begusarai",
    "Bhagalpur",
    "Bhojpur",
    "Buxar",
    "Darbhanga",
    "Gaya",
    "Gopalganj",
    "Jamui",
    "Jehanabad",
    "Kaimur",
    "Katihar",
    "Khagaria",
    "Kishanganj",
    "Lakhisarai",
    "Madhepura",
    "Madhubani",
    "Munger",
    "Muzaffarpur",
    "Nalanda",
    "Nawada",
    "Patna",
    "Purnia",
    "Rohtas",
    "Saharsa",
    "Samastipur",
    "Saran",
    "Sheikhpura",
    "Sheohar",
    "Sitamarhi",
    "Siwan",
    "Supaul",
    "Vaishali"
  ],
  "Chhattisgarh": [
    "Balod",
    "Bastar",
    "Bemetara",
    "Bilaspur",
    "Dantewada",
    "Dhamtari",
    "Durg",
    "Gariaband",
    "Janjgir-Champa",
    "Jashpur",
    "Kabirdham",
    "Kanker",
    "Kondagaon",
    "Korba",
    "Mahasamund",
    "Mungeli",
    "Raigarh",
    "Raipur",
    "Rajnandgaon",
    "Sukma",
    "Surajpur",
    "Surguja"
  ],
  "Goa": [
    "North Goa",
    "South Goa"
  ],
  "Gujarat": [
    "Ahmedabad",
    "Amreli",
    "Anand",
    "Banaskantha",
    "Bharuch",
    "Bhavnagar",
    "Chhota Udaipur",
    "Dang",
    "Devbhumi Dwarka",
    "Gandhinagar",
    "Gir Somnath",
    "Jamnagar",
    "Junagadh",
    "Kheda",
    "Morbi",
    "Narmada",
    "Navsari",
    "Patan",
    "Porbandar",
    "Rajkot",
    "Sabarkantha",
    "Surat",
    "Surendranagar",
    "Tapi",
    "Vadodara",
    "Valsad"
  ],
  "Haryana": [
    "Ambala",
    "Bhiwani",
    "Charkhi Dadri",
    "Faridabad",
    "Fatehabad",
    "Gurugram",
    "Hisar",
    "Jhajjar",
    "Jind",
    "Kaithal",
    "Karnal",
    "Kurukshetra",
    "Mahendragarh",
    "Nuh",
    "Palwal",
    "Panchkula",
    "Panipat",
    "Rewari",
    "Rohtak",
    "Sirsa",
    "Sonipat",
    "Yamunanagar"
  ],
  "Himachal Pradesh": [
    "Bilaspur",
    "Chamba",
    "Hamirpur",
    "Kangra",
    "Kullu",
    "Mandi",
    "Sirmaur",
    "Solan",
    "Una"
  ],
  "Jharkhand": [
    "Bokaro",
    "Chatra",
    "Deoghar",
    "Dhanbad",
    "Dumka",
    "Garhwa",
    "Giridih",
    "Godda",
    "Gumla",
    "Hazaribag",
    "Jamtara",
    "Khunti",
    "Latehar",
    "Lohardaga",
    "Pakur",
    "Ramgarh",
    "Ranchi"
  ],
  "Karnataka": [
    "Ballari",
    "Bangalore Rural",
    "Bangalore Urban",
    "Bidar",
    "Chitradurga",
    "Davanagere",
    "Dharwad",
    "Kalaburagi",
    "Hassan",
    "Haveri",
    "Kodagu",
    "Kolar",
    "Koppal",
    "Mandya",
    "Mysore",
    "Raichur",
    "Udupi",
    "Uttara Kannada",
    "Bijapur",
    "Yadgir"
  ],
  "Kerala": [
    "Alappuzha",
    "Ernakulam",
    "Idukki",
    "Kannur",
    "Kasaragod",
    "Kollam",
    "Kottayam",
    "Kozhikode",
    "Malappuram",
    "Palakkad",
    "Pathanamthitta",
    "Thiruvananthapuram",
    "Thrissur",
    "Wayanad"
  ],
  "Madhya Pradesh": [
    "Agar Malwa",
    "Alirajpur",
    "Anuppur",
    "Balaghat",
    "Barwani",
    "Betul",
    "Bhind",
    "Bhopal",
    "Burhanpur",
    "Chhatarpur",
    "Chhindwara",
    "Damoh",
    "Datia",
    "Dewas",
    "Dhar",
    "Dindori",
    "Guna",
    "Gwalior",
    "Harda",
    "Hoshangabad",
    "Indore",
    "Jabalpur",
    "Jhabua",
    "Katni",
    "Khandwa",
    "Khargone",
    "Mandla",
    "Mandsaur",
    "Morena",
    "Neemuch",
    "Panna",
    "Raisen",
    "Rajgarh",
    "Ratlam",
    "Rewa",
    "Sagar",
    "Satna",
    "Sehore",
    "Seoni",
    "Shahdol",
    "Shajapur",
    "Sheopur",
    "Shivpuri",
    "Sidhi",
    "Singrauli",
    "Tikamgarh",
    "Ujjain",
    "Umaria",
    "Vidisha"
  ],
  "Maharashtra": [
    "Akola",
    "Amravati",
    "Aurangabad",
    "Beed",
    "Bhandara",
    "Chandrapur",
    "Osmanabad",
    "Dhule",
    "Gadchiroli",
    "Gondia",
    "Hingoli",
    "Jalgaon",
    "Jalna",
    "Kolhapur",
    "Latur",
    "Mumbai City",
    "Mumbai Suburban",
    "Nanded",
    "Nandurbar",
    "Nagpur",
    "Nashik",
    "Palghar",
    "Parbhani",
    "Pune",
    "Raigad",
    "Ratnagiri",
    "Sangli",
    "Satara",
    "Solapur",
    "Thane",
    "Wardha",
    "Washim",
    "Yavatmal"
  ],
  "Meghalaya": [
    "East Garo Hills",
    "East Jaintia Hills",
    "East Khasi Hills",
    "Eastern West Khasi Hills",
    "North Garo Hills",
    "Ri Bhoi",
    "West Garo Hills",
    "West Khasi Hills"
  ],
  "Nagaland": [
    "Dimapur",
    "Kohima",
    "Mokokchung",
    "Mon",
    "Phek",
    "Tuensang",
    "Wokha"
  ],
  "Odisha": [
    "Bhadrak",
    "Balangir",
    "Bargarh",
    "Cuttack",
    "Debagarh",
    "Dhenkanal",
    "Ganjam",
    "Gajapati",
    "Jharsuguda",
    "Khordha",
    "Kendujhar",
    "Kalahandi",
    "Kandhamal",
    "Koraput",
    "Kendrapara",
    "Malkangiri",
    "Mayurbhanj",
    "Nuapada",
    "Nayagarh",
    "Puri",
    "Rayagada",
    "Sambalpur",
    "Sundargarh"
  ],
  "Punjab": [
    "Amritsar",
    "Barnala",
    "Bathinda",
    "Faridkot",
    "Fatehgarh Sahib",
    "Fazilka",
    "Gurdaspur",
    "Hoshiarpur",
    "Jalandhar",
    "Kapurthala",
    "Ludhiana",
    "Mansa",
    "Moga",
    "Pathankot",
    "Patiala",
    "Sangrur",
    "Tarn Taran"
  ],
  "Rajasthan": [
    "Ajmer",
    "Alwar",
    "Banswara",
    "Baran",
    "Barmer",
    "Bharatpur",
    "Bhilwara",
    "Bikaner",
    "Bundi",
    "Chittorgarh",
    "Churu",
    "Dausa",
    "Dholpur",
    "Dungarpur",
    "Hanumangarh",
    "Jaipur",
    "Jaisalmer",
    "Jalore",
    "Jhalawar",
    "Jhunjhunu",
    "Jodhpur",
    "Karauli",
    "Kota",
    "Nagaur",
    "Pali",
    "Pratapgarh",
    "Rajsamand",
    "Sawai Madhopur",
    "Sikar",
    "Sirohi",
    "Tonk",
    "Udaipur"
  ],

  "Tamil Nadu": [
    "Ariyalur",
    "Chennai",
    "Coimbatore",
    "Cuddalore",
    "Dharmapuri",
    "Dindigul",
    "Erode",
    "Kanyakumari",
    "Karur",
    "Krishnagiri",
    "Madurai",
    "Nagapattinam",
    "Nilgiris",
    "Namakkal",
    "Perambalur",
    "Pudukkottai",
    "Ramanathapuram",
    "Salem",
    "Sivaganga",
    "Tenkasi",
    "Tiruppur",
    "Tiruchirappalli",
    "Theni",
    "Tirunelveli",
    "Thanjavur",
    "Thoothukudi",
    "Tiruvallur",
    "Tiruvarur",
    "Tiruvannamalai",
    "Vellore",
    "Viluppuram",
    "Virudhunagar"
  ],
  "Telangana": [
    "Adilabad",
    "Hanamkonda",
    "Hyderabad",
    "Jangaon",
    "Kamareddy",
    "Karimnagar",
    "Khammam",
    "Mahabubabad",
    "Mahbubnagar",
    "Mancherial",
    "Medak",
    "Medchal–Malkajgiri",
    "Mulugu",
    "Nalgonda",
    "Nagarkurnool",
    "Narayanpet",
    "Nirmal",
    "Nizamabad",
    "Rajanna Sircilla",
    "Ranga Reddy",
    "Siddipet",
    "Suryapet",
    "Vikarabad",
    "Wanaparthy"
  ],
  "Tripura": [
    "Dhalai",
    "Gomati",
    "North Tripura",
    "Sepahijala",
    "South Tripura",
    "Unakoti",
    "West Tripura"
  ],
  "Uttar Pradesh": [
    "Agra",
    "Aligarh",
    "Ambedkar Nagar",
    "Auraiya",
    "Ayodhya",
    "Azamgarh",
    "Bahraich",
    "Ballia",
    "Balrampur",
    "Banda",
    "Barabanki",
    "Bareilly",
    "Basti",
    "Bhadohi",
    "Bijnor",
    "Budaun",
    "Chandauli",
    "Chitrakoot",
    "Deoria",
    "Etah",
    "Etawah",
    "Firozabad",
    "Ghaziabad",
    "Gonda",
    "Gorakhpur",
    "Hamirpur",
    "Hapur",
    "Hardoi",
    "Hathras",
    "Jalaun",
    "Jaunpur",
    "Jhansi",
    "Kaushambi",
    "Kannauj",
    "Kanpur Dehat",
    "Kheri",
    "Lalitpur",
    "Lucknow",
    "Mahoba",
    "Mainpuri",
    "Mathura",
    "Mau",
    "Meerut",
    "Mirzapur",
    "Moradabad",
    "Muzaffarnagar",
    "Pilibhit",
    "Pratapgarh",
    "Rampur",
    "Saharanpur",
    "Sambhal",
    "Shamli",
    "Siddharthnagar",
    "Sitapur",
    "Sonbhadra",
    "Sultanpur",
    "Unnao",
    "Varanasi"
  ],
  "Uttarakhand": [
    "Almora",
    "Champawat",
    "Dehradun",
    "Haridwar",
    "Nainital",
    "Pauri Garhwal",
    "Udham Singh Nagar",
    "Uttarkashi"
  ],
  "West Bengal": [
    "Alipurduar",
    "Bankura",
    "Birbhum",
    "Cooch Behar",
    "Hooghly",
    "Howrah",
    "Jalpaiguri",
    "Jhargram",
    "Kolkata",
    "Murshidabad",
    "Nadia",
    "North 24 Parganas",
    "South 24 Parganas",
    "South Dinajpur"
  ],
  "Delhi": [
    "New Delhi",
    "South East Delhi"
  ],
  "Puducherry": [
    "Karaikal",
    "Puducherry",
    "Yanam"
  ]
}

        for state, districts in DATA_MAP.items():
            print(f"Processing State => {state}")

            # Cache existing stations
            station_cache = {s.station_code: s for s in Station.objects.filter(state=state)}
            cache_lock = threading.Lock()

            with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
                futures = []
                for district in districts:
                    futures.append(
                        executor.submit(
                            self.process_district,
                            state,
                            district,
                            start_date,
                            end_date,
                            station_cache,
                            cache_lock
                        )
                    )

                concurrent.futures.wait(futures)

        print("✔ Data Fetch Completed")

    def process_district(self, state, district, start_date, end_date, station_cache, cache_lock):
        BATCH_SIZE = 5000
        page = 0
        session = requests.Session()

        while True:
            close_old_connections()

            state_q = urllib.parse.quote(state)
            district_q = urllib.parse.quote(district)

            url = (
                f"https://indiawris.gov.in/Dataset/Ground Water Level?"
                f"stateName={state_q}&districtName={district_q}"
                f"&agencyName=CGWB&startdate={start_date}&enddate={end_date}"
                f"&download=false&page={page}&size={BATCH_SIZE}"
            )

            try:
                response = session.post(url, headers={'accept': 'application/json'}, timeout=25)
            except Exception as e:
                print(f"[{district}] ❌ Network Failed: {e}")
                return

            if response.status_code != 200:
                print(f"[{district}] ❌ API Error: {response.status_code}")
                return

            data = response.json().get("data", [])
            if not data:
                return

            print(f"[{district}] Fetched {len(data)}")

            ### ---- CREATE STATIONS ---- ###
            new_stations = []
            with cache_lock:
                for item in data:
                    code = item.get("stationCode")
                    if code and code not in station_cache:

                        new_stations.append(
                            Station(
                                station_code=item.get("stationCode"),
                                station_name=item.get("stationName"),
                                latitude=item.get("latitude") or None,
                                longitude=item.get("longitude") or None,
                                well_depth=item.get("wellDepth") or None,
                                well_type=item.get("wellType"),
                                aquifer_type=item.get("wellAquiferType"),
                                state=item.get("state") or state,
                                district=item.get("district") or district
                            )
                        )

                        station_cache[code] = None

                if new_stations:
                    Station.objects.bulk_create(new_stations, ignore_conflicts=True)
                    created_codes = [s.station_code for s in new_stations]

                    for s in Station.objects.filter(station_code__in=created_codes):
                        station_cache[s.station_code] = s

                    print(f"[{district}] ➕ Stations Added: {len(new_stations)}")

            ### ---- CREATE WATER READINGS ---- ###
            readings = []
            for item in data:
                code = item.get("stationCode")
                station = station_cache.get(code)

                if not station:
                    continue

                try:
                    readings.append(
                        WaterReading(
                            station=station,
                            value=item.get("dataValue"),
                            timestamp=datetime.fromisoformat(item.get("dataTime")),
                            unit=item.get("unit") or "m"
                        )
                    )
                except:
                    continue

            if readings:
                WaterReading.objects.bulk_create(readings, ignore_conflicts=True)
                print(f"[{district}] 💾 Saved Readings: {len(readings)}")

            if len(data) < BATCH_SIZE:
                return

            page += 1
