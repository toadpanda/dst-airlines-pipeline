#import os
#import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

# Import utils
from api_utils import run_batch_ingestion
from pipeline_utils import (
    generate_dim_time,
    generate_dim_date,

    clean_countries_db,
    clean_cities_db,
    clean_airports_db,
    clean_airlines_db,
    clean_aircraft_db,
    clean_flights,
    clean_schedules,

    build_fact_flight,
    load_incremental_flights,

    enrich_dim_aircraft,
    enrich_dim_airlines,
)


# =========================================================================
# PATH CONFIGURATION
# =========================================================================
# Anchor to the directory containing main_pipeline.py (etl_pipeline/)
BASE_DIR = Path(__file__).resolve().parent

# Define Project Root
PROJECT_ROOT = BASE_DIR.parent


# =========================================================================
# DATABASE CONFIGURATION
# =========================================================================
DB_NAME = "airlines_warehouse.db"

# Route the files to their designated folders
DB_DEST_DIR = PROJECT_ROOT / "database"
DB_PATH = DB_DEST_DIR / DB_NAME
SCHEMA_PATH = PROJECT_ROOT / "database_schema" / "schema.sql"

# Ensure the 'database' directory exists
DB_DEST_DIR.mkdir(parents=True, exist_ok=True)

# Check if the database file already exists
db_exists = DB_PATH.exists()

# Create SQLAlchemy engine connection (using .as_posix() for OS compatibility)
engine = create_engine(f"sqlite:///{DB_PATH.as_posix()}")

# =========================================================================
# INITIALIZATION (Runs only if DB doesn't exist)
# =========================================================================
if not db_exists:
    print("Initial run detected: Creating database schema and base dimensions...")

    # Execute schema.sql file to build tables, PKs, and FKs
    with open(SCHEMA_PATH, "r") as f:
        schema_sql = f.read()

    with engine.begin() as conn:
        # SQLite execution requires raw connection execution for multi-statement DDL scripts
        raw_conn = conn.connection
        cursor = raw_conn.cursor()
        cursor.executescript(schema_sql)
        raw_conn.commit()

    print("Schema created successfully!")

    # Generate and load static Date and Time dimensions
    dim_date = generate_dim_date()
    dim_date.to_sql('dim_date', engine, if_exists='append', index=False)

    dim_time = generate_dim_time()
    dim_time.to_sql('dim_time', engine, if_exists='append', index=False)

    print("Static time dimensions populated.")

    print("Ingesting initial datasets from AirLabs API...")
    # Define endpoints and their specific requirements
    ingestion_plan = {
        #'flights': {},
        # 'schedules': {'dep_iata': 'LHR'}, # dep_iata/dep_icao
        # 'schedules': {'arr_iata': 'LHR'}, # arr_iata/arr_icao
        'airportsDB': {},
        'airlinesDB': {},
        'citiesDB': {},
        'countriesDB': {},
        'fleetsDB': {'airline_icao': 'BAW'},
    }

    df = run_batch_ingestion(ingestion_plan, verbose=False)

    print("Transforming baseline datasets...")
    # Create Independent Dimensions
    dim_countries = clean_countries_db(df['countriesDB'])
    dim_cities = clean_cities_db(df['citiesDB'])
    dim_airports = clean_airports_db(df['airportsDB'])
    dim_airlines = clean_airlines_db(df['airlinesDB'])
    dim_aircrafts = clean_aircraft_db(df['fleetsDB'])

    # Create Dependent Fact Table & Telemetry/Time Dimension
    # fact_flights, dim_flight_position, df_live_aircraft_patch = clean_flights(df['flights'])

    # ================================
    # Load Dim & Fact Tables into SQL
    print("Loading dimension and fact tables into the database...")

    # Independent Dimensions first (so foreign keys are ready)
    dim_countries.to_sql('dim_country', engine, if_exists='append', index=False)
    dim_cities.to_sql('dim_city', engine, if_exists='append', index=False)
    dim_airports.to_sql('dim_airport', engine, if_exists='append', index=False)
    dim_airlines.to_sql('dim_airline', engine, if_exists='append', index=False)
    dim_aircrafts.to_sql('dim_aircraft', engine, if_exists='append', index=False)

    # Dependent Dimensions & Fact
    # fact_flights.to_sql('fact_flight', engine, if_exists='append', index=False)
    # dim_flight_position.to_sql('dim_flight_position', engine, if_exists='append', index=False)

    print("Initial setup complete! Database created and populated successfully.")

else:
    print("Existing database found. Skipping schema creation. Ready for incremental append.")

# =========================================================================
# DAILY INCREMENTAL RUN (Runs every execution)
# =========================================================================
print("Starting routine flight & schedule ingestion...")

# Extract only fresh live flights on daily runs
daily_plan = {
    'flights': {},
    'schedules': {'dep_iata': 'LHR'}, # dep_iata/dep_icao
    'schedules': {'arr_iata': 'LHR'}, # arr_iata/arr_icao
}
df_raw = run_batch_ingestion(daily_plan, verbose=False)

if df_raw.get('flights') is not None and not df_raw['flights'].empty:
    print("Cleaning live telemetry and schedules...")

    # Clean the raw data
    fact_flights, dim_flight_position, df_live_aircraft_patch = clean_flights(df_raw['flights'])

    if df_raw.get('schedules') is not None and not df_raw['schedules'].empty:
        clean_scheds = clean_schedules(df_raw['schedules'])
    else:
        # Failsafe, if schedules endpoint returns nothing
        clean_scheds = pd.DataFrame(columns=['flight_icao'])

    # Merge: Attach schedules to the live flights
    final_fact_flights = build_fact_flight(fact_flights, clean_scheds)

    # ================================================
    # Enrichment 1: Update the aircraft dimension with live patch
    try:
        print("Checking for new aircraft data to enrich dim_aircraft...")
        existing_aircraft = pd.read_sql("SELECT * FROM dim_aircraft;", engine)

        # Get the full, updated DataFrame from enrich_dim_aircraft
        dim_aircraft_enriched = enrich_dim_aircraft(existing_aircraft, df_live_aircraft_patch)

        # Clear the existing data without touching the table schema
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM dim_aircraft;"))

        # Append the full enriched DataFrame back into the empty table
        dim_aircraft_enriched.to_sql('dim_aircraft', engine, if_exists='append', index=False)
        print(f"Aircraft dimension updated successfully with {len(dim_aircraft_enriched)} total records.")

    except Exception as e:
        print(f"Skipping aircraft enrichment due to error: {e}")

    # ================================================
    # Enrichment 2: Update the aircraft dimension with live patch
    try:
        print("Checking live flights to patch missing Airline data...")
        existing_airlines = pd.read_sql("SELECT * FROM dim_airline;", engine)

        # Get the full, updated DataFrame
        dim_airline_enriched = enrich_dim_airlines(existing_airlines, df_raw['flights'])

        # Clear existing data
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM dim_airline;"))

        # Append the full enriched DataFrame
        dim_airline_enriched.to_sql('dim_airline', engine, if_exists='append', index=False)
        print("Airline dimension updated successfully.")

    except Exception as e:
        print(f"Skipping aircraft enrichment due to error: {e}")

    # =========================================================================
    # DATABASE LOAD
    print("Pushing incremental data to the data warehouse...")
    added_flights, added_telemetry = load_incremental_flights(engine, final_fact_flights, dim_flight_position)

    print("Pipeline run completed successfully!")
    print(f"Audit: Added {added_flights} new flights and {added_telemetry} telemetry points.")

else:
    print("No flight data returned from API today. Pipeline aborted.")


### Automate execution
### f.e. crontab entry running main_pipeline.py daily at 05:00 AM
### 0 2 * * * /usr/bin/python3 /path/to/project/main_pipeline.py

"""
Handle Primary Key Conflicts on Incremental Appends:
If your daily flight pull generates surrogate integer keys starting from 1 every time you run it,
SQLite will throw a UNIQUE constraint failed error on the second day because ID 1 already exists.

Solution:
If your fact_flights table uses SQLite's built-in INTEGER PRIMARY KEY AUTOINCREMENT,
make sure you drop the explicit flight_id column right before calling .to_sql(),
allowing SQLite to automatically assign the next incremental integer sequence (... 133, 134, 135 ...) to your new daily rows!
"""

