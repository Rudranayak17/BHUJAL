import requests
import time
import urllib.parse
import threading
import concurrent.futures
from collections import defaultdict
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from django.core.management.base import BaseCommand
from django.db import connection, close_old_connections
# Ensure these imports match your actual app name
from Dashboard.models import Station, GroundwaterLevel, DistrictLog

class Command(BaseCommand):
    help = "High-Performance Real-time fetcher: Runs parallel requests for the current date."

    def add_arguments(self, parser):
        parser.add_argument(
            '--generate-map',
            action='store_true',
            help='Print the DATA_MAP dictionary from the database DistrictLogs and exit.',
        )

    def handle(self, *args, **options):
        # --- 0. OPTIONAL: GENERATE MAP AND EXIT ---
        if options['generate_map']:
            self.stdout.write(self.style.SUCCESS("--- Generating DATA_MAP from Database ---"))
            
            logs = DistrictLog.objects.all().order_by('state', 'district')
            
            if not logs.exists():
                self.stdout.write(self.style.WARNING("No DistrictLogs found in database."))
                return

            output_map = defaultdict(list)
            for log in logs:
                output_map[log.state].append(log.district)

            print("DATA_MAP = {")
            for state, districts in output_map.items():
                # Use repr() to format the list safely with quotes
                print(f"    '{state}': {districts},")
            print("}")
            
            self.stdout.write(self.style.SUCCESS("--- Copy the above dictionary into your script ---"))
            return

        # --- 1. AUTOMATIC DATE CONFIGURATION ---
        today = datetime.now()
        yesterday = today - timedelta(days=1)

        start_date = '2025-08-03'
        end_date = today.strftime("%Y-%m-%d")
        
        self.stdout.write(self.style.SUCCESS(f"--- AUTO-MODE: Fetching data for {today} ---"))

        # --- 2. THE DATA MAP (Horizontal Format) ---
        DATA_MAP = {
  "Andhra Pradesh": [ "Alluri Sitharama Raju", "Ananthapuramu", "Annamayya", "Bapatla", "Chittoor", "East Godavari", "Eluru", "Guntur", "Krishna", "Kurnool", "Nandyal", "Nellore", "Palnadu", "Prakasam", "Srikakulam", "Sri Sathya Sai", "Visakhapatnam", "Vizianagaram", "West Godavari" ], "Arunachal Pradesh": [ "Changlang", "East Siang", "Lohit", "Lower Dibang Valley", "Lower Subansiri", "Namsai", "Papum Pare", "Tirap" ], "Assam": [ "Baksa", "Barpeta", "Biswanath", "Bongaigaon", "Cachar", "Chirang", "Darrang", "Dhemaji", "Dhubri", "Dibrugarh", "Goalpara", "Golaghat", "Hailakandi", "Hojai", "Jorhat", "Kamrup", "Kamrup Metropolitan", "Karbi Anglong", "Karimganj", "Kokrajhar", "Lakhimpur", "Nagaon", "Nalbari", "Sonitpur", "Tinsukia", "Udalguri" ], "Bihar": [ "Araria", "Aurangabad", "Banka", "Begusarai", "Bhagalpur", "Bhojpur", "Buxar", "Darbhanga", "Gaya", "Gopalganj", "Jamui", "Jehanabad", "Kaimur", "Katihar", "Khagaria", "Kishanganj", "Lakhisarai", "Madhepura", "Madhubani", "Munger", "Muzaffarpur", "Nalanda", "Nawada", "Patna", "Purnia", "Rohtas", "Saharsa", "Samastipur", "Saran", "Sheikhpura", "Sheohar", "Sitamarhi", "Siwan", "Supaul", "Vaishali" ], "Chhattisgarh": [ "Balod", "Bastar", "Bemetara", "Bilaspur", "Dantewada", "Dhamtari", "Durg", "Gariaband", "Janjgir-Champa", "Jashpur", "Kabirdham", "Kanker", "Kondagaon", "Korba", "Mahasamund", "Mungeli", "Raigarh", "Raipur", "Rajnandgaon", "Sukma", "Surajpur", "Surguja" ], "Goa": [ "North Goa", "South Goa" ], "Gujarat": [ "Ahmedabad", "Amreli", "Anand", "Banaskantha", "Bharuch", "Bhavnagar", "Chhota Udaipur", "Dang", "Devbhumi Dwarka", "Gandhinagar", "Gir Somnath", "Jamnagar", "Junagadh", "Kheda", "Morbi", "Narmada", "Navsari", "Patan", "Porbandar", "Rajkot", "Sabarkantha", "Surat", "Surendranagar", "Tapi", "Vadodara", "Valsad" ], "Haryana": [ "Ambala", "Bhiwani", "Charkhi Dadri", "Faridabad", "Fatehabad", "Gurugram", "Hisar", "Jhajjar", "Jind", "Kaithal", "Karnal", "Kurukshetra", "Mahendragarh", "Nuh", "Palwal", "Panchkula", "Panipat", "Rewari", "Rohtak", "Sirsa", "Sonipat", "Yamunanagar" ], "Himachal Pradesh": [ "Bilaspur", "Chamba", "Hamirpur", "Kangra", "Kullu", "Mandi", "Sirmaur", "Solan", "Una" ], "Jharkhand": [ "Bokaro", "Chatra", "Deoghar", "Dhanbad", "Dumka", "Garhwa", "Giridih", "Godda", "Gumla", "Hazaribag", "Jamtara", "Khunti", "Latehar", "Lohardaga", "Pakur", "Ramgarh", "Ranchi" ], "Karnataka": [ "Ballari", "Bangalore Rural", "Bangalore Urban", "Bidar", "Chitradurga", "Davanagere", "Dharwad", "Kalaburagi", "Hassan", "Haveri", "Kodagu", "Kolar", "Koppal", "Mandya", "Mysore", "Raichur", "Udupi", "Uttara Kannada", "Bijapur", "Yadgir" ], "Kerala": [ "Alappuzha", "Ernakulam", "Idukki", "Kannur", "Kasaragod", "Kollam", "Kottayam", "Kozhikode", "Malappuram", "Palakkad", "Pathanamthitta", "Thiruvananthapuram", "Thrissur", "Wayanad" ], "Madhya Pradesh": [ "Agar Malwa", "Alirajpur", "Anuppur", "Balaghat", "Barwani", "Betul", "Bhind", "Bhopal", "Burhanpur", "Chhatarpur", "Chhindwara", "Damoh", "Datia", "Dewas", "Dhar", "Dindori", "Guna", "Gwalior", "Harda", "Hoshangabad", "Indore", "Jabalpur", "Jhabua", "Katni", "Khandwa", "Khargone", "Mandla", "Mandsaur", "Morena", "Neemuch", "Panna", "Raisen", "Rajgarh", "Ratlam", "Rewa", "Sagar", "Satna", "Sehore", "Seoni", "Shahdol", "Shajapur", "Sheopur", "Shivpuri", "Sidhi", "Singrauli", "Tikamgarh", "Ujjain", "Umaria", "Vidisha" ], "Maharashtra": [ "Akola", "Amravati", "Aurangabad", "Beed", "Bhandara", "Chandrapur", "Osmanabad", "Dhule", "Gadchiroli", "Gondia", "Hingoli", "Jalgaon", "Jalna", "Kolhapur", "Latur", "Mumbai City", "Mumbai Suburban", "Nanded", "Nandurbar", "Nagpur", "Nashik", "Palghar", "Parbhani", "Pune", "Raigad", "Ratnagiri", "Sangli", "Satara", "Solapur", "Thane", "Wardha", "Washim", "Yavatmal" ], "Meghalaya": [ "East Garo Hills", "East Jaintia Hills", "East Khasi Hills", "Eastern West Khasi Hills", "North Garo Hills", "Ri Bhoi", "West Garo Hills", "West Khasi Hills" ], "Nagaland": [ "Dimapur", "Kohima", "Mokokchung", "Mon", "Phek", "Tuensang", "Wokha" ], "Odisha": [ "Bhadrak", "Balangir", "Bargarh", "Cuttack", "Debagarh", "Dhenkanal", "Ganjam", "Gajapati", "Jharsuguda", "Khordha", "Kendujhar", "Kalahandi", "Kandhamal", "Koraput", "Kendrapara", "Malkangiri", "Mayurbhanj", "Nuapada", "Nayagarh", "Puri", "Rayagada", "Sambalpur", "Sundargarh" ], "Punjab": [ "Amritsar", "Barnala", "Bathinda", "Faridkot", "Fatehgarh Sahib", "Fazilka", "Gurdaspur", "Hoshiarpur", "Jalandhar", "Kapurthala", "Ludhiana", "Mansa", "Moga", "Pathankot", "Patiala", "Sangrur", "Tarn Taran" ], "Rajasthan": [ "Ajmer", "Alwar", "Banswara", "Baran", "Barmer", "Bharatpur", "Bhilwara", "Bikaner", "Bundi", "Chittorgarh", "Churu", "Dausa", "Dholpur", "Dungarpur", "Hanumangarh", "Jaipur", "Jaisalmer", "Jalore", "Jhalawar", "Jhunjhunu", "Jodhpur", "Karauli", "Kota", "Nagaur", "Pali", "Pratapgarh", "Rajsamand", "Sawai Madhopur", "Sikar", "Sirohi", "Tonk", "Udaipur" ], "Tamil Nadu": [ "Ariyalur", "Chennai", "Coimbatore", "Cuddalore", "Dharmapuri", "Dindigul", "Erode", "Kanyakumari", "Karur", "Krishnagiri", "Madurai", "Nagapattinam", "Nilgiris", "Namakkal", "Perambalur", "Pudukkottai", "Ramanathapuram", "Salem", "Sivaganga", "Tenkasi", "Tiruppur", "Tiruchirappalli", "Theni", "Tirunelveli", "Thanjavur", "Thoothukudi", "Tiruvallur", "Tiruvarur", "Tiruvannamalai", "Vellore", "Viluppuram", "Virudhunagar" ], "Telangana": [ "Adilabad", "Hanamkonda", "Hyderabad", "Jangaon", "Kamareddy", "Karimnagar", "Khammam", "Mahabubabad", "Mahbubnagar", "Mancherial", "Medak", "Medchal–Malkajgiri", "Mulugu", "Nalgonda", "Nagarkurnool", "Narayanpet", "Nirmal", "Nizamabad", "Rajanna Sircilla", "Ranga Reddy", "Siddipet", "Suryapet", "Vikarabad", "Wanaparthy" ], "Tripura": [ "Dhalai", "Gomati", "North Tripura", "Sepahijala", "South Tripura", "Unakoti", "West Tripura" ], "Uttar Pradesh": [ "Agra", "Aligarh", "Ambedkar Nagar", "Auraiya", "Ayodhya", "Azamgarh", "Bahraich", "Ballia", "Balrampur", "Banda", "Barabanki", "Bareilly", "Basti", "Bhadohi", "Bijnor", "Budaun", "Chandauli", "Chitrakoot", "Deoria", "Etah", "Etawah", "Firozabad", "Ghaziabad", "Gonda", "Gorakhpur", "Hamirpur", "Hapur", "Hardoi", "Hathras", "Jalaun", "Jaunpur", "Jhansi", "Kaushambi", "Kannauj", "Kanpur Dehat", "Kheri", "Lalitpur", "Lucknow", "Mahoba", "Mainpuri", "Mathura", "Mau", "Meerut", "Mirzapur", "Moradabad", "Muzaffarnagar", "Pilibhit", "Pratapgarh", "Rampur", "Saharanpur", "Sambhal", "Shamli", "Siddharthnagar", "Sitapur", "Sonbhadra", "Sultanpur", "Unnao", "Varanasi" ], "Uttarakhand": [ "Almora", "Champawat", "Dehradun", "Haridwar", "Nainital", "Pauri Garhwal", "Udham Singh Nagar", "Uttarkashi" ], "West Bengal": [ "Alipurduar", "Bankura", "Birbhum", "Cooch Behar", "Hooghly", "Howrah", "Jalpaiguri", "Jhargram", "Kolkata", "Murshidabad", "Nadia", "North 24 Parganas", "South 24 Parganas", "South Dinajpur" ], "Delhi": [ "New Delhi", "South East Delhi" ], "Puducherry": [ "Karaikal", "Puducherry", "Yanam" ]}
        
        # --- NEW: ERROR TRACKING SETUP ---
        failed_districts = []
        error_list_lock = threading.Lock() # Lock for thread-safe list updates

        # --- 3. EXECUTION LOOP ---
        for state, districts in DATA_MAP.items():
            self.stdout.write(self.style.MIGRATE_HEADING(f"--- Processing State: {state} ---"))

            print(f"Caching existing stations for {state}...")
            station_cache = {s.station_name: s for s in Station.objects.filter(state=state)}
            print(f"Loaded {len(station_cache)} stations into memory.")
            
            cache_lock = threading.Lock()

            with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
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
                            cache_lock,
                            failed_districts,      # PASSED TO WORKER
                            error_list_lock        # PASSED TO WORKER
                        )
                    )
                concurrent.futures.wait(futures)

        self.stdout.write(self.style.SUCCESS(f"Finished auto-fetch for {today}"))

        # --- FINAL: PRINT FAILED DISTRICTS REPORT ---
        if failed_districts:
            self.stdout.write(self.style.ERROR("\n--- FAILED DISTRICTS REPORT (Network/Timeout) ---"))
            # Sort the output by state for readability
            failed_districts.sort(key=lambda x: x['state'])
            
            for item in failed_districts:
                self.stdout.write(self.style.ERROR(f"[{item['state']} - {item['district']}] Error: {item['error']}"))
            self.stdout.write(self.style.ERROR("--------------------------------------------------"))
        else:
            self.stdout.write(self.style.SUCCESS("\nNo districts reported critical network or timeout failures."))


    def process_district(self, state, district, start_date, end_date, station_cache, cache_lock, failed_districts, error_list_lock):
        """
        Worker function that processes a single district.
        Running in a separate thread.
        
        New Arguments:
        - failed_districts: Shared list to log errors.
        - error_list_lock: Lock for thread-safe access to failed_districts.
        """
        BATCH_SIZE = 5000
        headers = {'accept': 'application/json'}
        page = 0
        
        logged_success = False 
        
        # --- ROBUST SESSION SETUP ---
        session = requests.Session()
        # Retries: Total 3 attempts, with exponential backoff
        retries = Retry(total=1, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        session.mount('https://', HTTPAdapter(max_retries=retries))

        close_old_connections()

        while True:
            state_q = urllib.parse.quote(state)
            district_q = urllib.parse.quote(district)

            url = (
                f"https://indiawris.gov.in/Dataset/Ground Water Level?"
                f"stateName={state_q}&districtName={district_q}"
                f"&agencyName=CGWB&startdate={start_date}&enddate={end_date}"
                f"&download=false&page={page}&size={BATCH_SIZE}"
            )

            try:
                net_start = time.time()
                # INCREASED TIMEOUT TO 60 SECONDS
                response = session.post(url, headers=headers, timeout=60)
                net_time = time.time() - net_start
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"[{district}] Network error (Giving up): {e}"))
                
                # --- NEW: Log the failure to the shared list ---
                with error_list_lock:
                    failed_districts.append({
                        'state': state,
                        'district': district,
                        'error': str(e)
                    })
                break

            if response.status_code != 200:
                self.stdout.write(self.style.WARNING(f"[{district}] API Error {response.status_code}"))
                break

            data = response.json().get("data", [])
            
            if not data:
                break 

            self.stdout.write(f"[{district}] Fetched {len(data)} records (Page {page}) in {net_time:.2f}s")

            # --- SAVE DISTRICT LOG ---
            if not logged_success and len(data) > 0:
                try:
                    obj, created = DistrictLog.objects.get_or_create(
                        state=state, 
                        district=district
                    )
                    if created:
                        print(f"  >>> [{district}] First time fetching data! Added to DistrictLog.")
                    logged_success = True
                except Exception as e:
                    print(f"  >>> [{district}] Warning: Could not update log: {e}")

            # --- STEP 1: CREATE MISSING STATIONS ---
            new_stations_to_create = []
            items_needing_check = [i for i in data if i.get('stationName')]
            
            with cache_lock:
                for item in items_needing_check: 
                    s_name = item.get('stationName')
                    if s_name and s_name not in station_cache:
                        new_stations_to_create.append(
                            Station(station_name=s_name, state=state, district=district)
                        )
                        station_cache[s_name] = None 

                if new_stations_to_create:
                    Station.objects.bulk_create(new_stations_to_create, ignore_conflicts=True)
                    created_names = [s.station_name for s in new_stations_to_create]
                    new_db_stations = Station.objects.filter(station_name__in=created_names, state=state)
                    for s in new_db_stations:
                        station_cache[s.station_name] = s
                    
                    print(f"  [{district}] -> Created {len(new_stations_to_create)} new stations.")

            # --- STEP 2: PREPARE RECORDS ---
            groundwater_records = []
            for item in data:
                s_name = item.get('stationName')
                try:
                    dt = datetime.fromisoformat(item.get('dataTime'))
                    depth = item.get('dataValue')
                    
                    station_obj = station_cache.get(s_name)

                    if station_obj:
                        groundwater_records.append(
                            GroundwaterLevel(
                                station=station_obj,
                                data_time=dt,
                                depth=depth
                            )
                        )
                except Exception:
                    continue

            # --- STEP 3: BULK INSERT ---
            if groundwater_records:
                db_start = time.time()
                GroundwaterLevel.objects.bulk_create(groundwater_records, ignore_conflicts=True)
                db_time = time.time() - db_start
                self.stdout.write(self.style.SUCCESS(f"  [{district}] -> Saved {len(groundwater_records)} records in {db_time:.4f}s"))

            if len(data) < BATCH_SIZE:
                break
            page += 1