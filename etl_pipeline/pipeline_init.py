from pathlib import Path
from sqlalchemy import create_engine

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
# CONFIGURATION TOGGLES
# =========================================================================
VERBOSE_PIPELINE = True  # Toggle True to see detailed step-by-step pipeline telemetry


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

    # Generate and load static Date and Time dimensions (Passing verbose flag)
    if VERBOSE_PIPELINE:
        print("\n----- Generating Static Dimensions -----")

    dim_date = generate_dim_date(verbose=VERBOSE_PIPELINE)
    dim_date.to_sql('dim_date', engine, if_exists='append', index=False)

    dim_time = generate_dim_time(verbose=VERBOSE_PIPELINE)
    dim_time.to_sql('dim_time', engine, if_exists='append', index=False)

    print("Static time dimensions populated.")

    print("Ingesting initial datasets from AirLabs API...")
    # Define endpoints and their specific requirements
    ingestion_plan = {
        'airportsDB': {},
        'airlinesDB': {},
        'citiesDB': {},
        'countriesDB': {},
        'fleetsDB': {'airline_icao': 'BAW'},
    }

    df = run_batch_ingestion(ingestion_plan, verbose=VERBOSE_PIPELINE)

    if VERBOSE_PIPELINE:
        print("\nTransforming Baseline Datasets...")

    # Create Independent Dimensions
    dim_countries = clean_countries_db(df['countriesDB'], verbose=VERBOSE_PIPELINE)
    dim_cities = clean_cities_db(df['citiesDB'], verbose=VERBOSE_PIPELINE)
    dim_airports = clean_airports_db(df['airportsDB'], verbose=VERBOSE_PIPELINE)
    dim_airlines = clean_airlines_db(df['airlinesDB'], verbose=VERBOSE_PIPELINE)
    dim_aircrafts = clean_aircraft_db(df['fleetsDB'], verbose=VERBOSE_PIPELINE)

    # ================================
    # Load Dim & Fact Tables into SQL
    print("Loading dimension and fact tables into the database...")

    # Independent Dimensions first (so foreign keys are ready)
    dim_countries.to_sql('dim_country', engine, if_exists='append', index=False)
    dim_cities.to_sql('dim_city', engine, if_exists='append', index=False)
    dim_airports.to_sql('dim_airport', engine, if_exists='append', index=False)
    dim_airlines.to_sql('dim_airline', engine, if_exists='append', index=False)
    dim_aircrafts.to_sql('dim_aircraft', engine, if_exists='append', index=False)

    print("Initial setup complete! Database created and populated successfully.")

else:
    print("Existing database found. Skipping initialization.")