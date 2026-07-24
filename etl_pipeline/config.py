import os
from dotenv import load_dotenv

# Point to the root directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '../.env'))

# Set API_KEY
AIRLABS_API_KEY = os.getenv("AIRLABS_API_KEY")

# Set BASE_URL
BASE_URL = 'https://airlabs.co/api/v9'

# Map Endpoints
ENDPOINTS = {
    'flights': 'flights',           # Real-Time Flights
#    'flight': 'flight',             # Flight Info
    'schedules': 'schedules',       # Airport Schedules
    'airlinesDB': 'airlines',         # Airlines DB
    'airportsDB': 'airports',         # Airport DB
    'citiesDB': 'cities',             # City DB
    'fleetsDB': 'fleets',             # DB for basic & minimum required airplanes information for every airline in the world
    'countriesDB': 'countries',        # Countries DB
#    'timezonesDB': 'timezones'          # Time Zone List
}

# Safe-Check
if not AIRLABS_API_KEY:
    print("Warning: AIRLABS_API_KEY not found in the .env file.")