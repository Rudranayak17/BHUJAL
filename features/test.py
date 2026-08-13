import requests

url = "https://indiawris.gov.in/Dataset/Ground Water Level?stateName=Madhya%20Pradesh&districtName=Jabalpur&agencyName=CGWB&startdate=2024-12-01&enddate=2024-12-05&download=false&page=0&size=5"
url2 = "https://indiawris.gov.in/Dataset/RainFall?stateName=Madhya%20Pradesh&districtName=Jabalpur&agencyName=CWC&startdate=2024-12-01&enddate=2024-12-05&download=false&page=0&size=5"

headers = {'accept': 'application/json'}

response1 = requests.post(url, headers=headers)
response2 = requests.post(url2,headers=headers)
print("GROUND WATER:\n")
print(response1.status_code)
print(response1.json())
print("RAINWATER:\n")
print(response2.status_code)
print(response2.json())