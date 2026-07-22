import pandas as pd
import uuid
import numpy as np

# =========================================================================
# CLEAN /airlinesDB -> DIM_AIRLINES
# =========================================================================

def clean_airlines_db(df):
    """
    Cleans airline data and formats it for the DIM_AIRLINES dimension table.
    """
    original_count = len(df)
    print(f"Original records from /airlines: {original_count}")

    # Only keep rows with the primary ID (ICAO)
    cleaned_df = df.dropna(subset=['icao_code']).copy()
    print(f"Count after keeping non-null 'icao_code' rows: {len(cleaned_df)}")

    # Standardize: Fill remaining single-column nulls in 'iata_code' with '000'
    # This prevents 'NULL' from breaking joins in our SQL database
    cleaned_df['iata_code'] = cleaned_df['iata_code'].fillna('000')

    ## Deduplication
    # Make sure every row is a unique airline, by using the Primary Key (icao_code).
    cleaned_df = cleaned_df.drop_duplicates(subset=['icao_code'])

    # Rename Columns
    cleaned_df = cleaned_df.rename(columns={'name': 'airline_name'}).fillna('UNKNOWN_AIRLINE')

    ## Finalize: Select only the columns that we need in our clean dimension table
    final_cols = ['icao_code', 'iata_code', 'airline_name']
    dim_airlines = cleaned_df[final_cols].copy()

    print(f"Final unique airline records for DIM_AIRLINES: {len(dim_airlines)}")

    return dim_airlines


# =========================================================================
# CLEAN /airportsDB -> DIM_AIRPORTS
# =========================================================================

def clean_airports_db(df):
    """
    Cleans airport data and formats it for the DIM_AIRPORT dimension table.
    """
    original_count = len(df)
    print(f"Original records from /airports: {original_count}")

    # Filter: Only keep rows where the Primary Key (icao_code) exists
    # And ensure required geometric data (lat/lng) is present
    cleaned_df = df.dropna(subset=['icao_code', 'lat', 'lng']).copy()

    # Safeguard: Drop duplicates based on Primary Key (icao_code)
    cleaned_df = cleaned_df.drop_duplicates(subset=['icao_code'])

    # Fill missing iata_code with '000' and format into string
    cleaned_df['iata_code'] = cleaned_df['iata_code'].fillna('000').astype(str)

    # Rename columns
    cleaned_df = cleaned_df.rename(columns={
        'name': 'airport_name',
        'lat': 'latitude',
        'lng': 'longitude',
    })

    # Select: Keep only columns defined in our schema
    final_cols = ['airport_name', 'icao_code', 'iata_code', 'latitude', 'longitude', 'country_code']
    dim_airports = cleaned_df[final_cols].copy()

    print(f"Unique airports for DIM_AIRPORT: {len(dim_airports)}")

    return dim_airports


# =========================================================================
# CLEAN /fleetsDB -> DIM_AIRCRAFTS
# =========================================================================

def clean_aircraft_db(df):
    """
    Cleans fleet dimension table by removing records without standard identifiers
    and aligning columns with the DIM_AIRCRAFT schema.
    """
    original_count = len(df)
    print(f"Original records from /fleets: {original_count}")

    # Drop rows where hex is null (= Primary Key of dim_aircraft)
    cleaned_df = df.dropna(subset=['hex']).copy()
    count_after_hex_drop = len(cleaned_df)
    print(f"Dropped {original_count - count_after_hex_drop} because of missing airplane_hex.")

    # Fill missing reg_number, aircraft_icao and aircraft_iata with placeholder
    cleaned_df['reg_number'] = cleaned_df['reg_number'].fillna('UNKNOWN_REG')
    cleaned_df['icao'] = cleaned_df['icao'].fillna('000')
    cleaned_df['iata'] = cleaned_df['iata'].fillna('000')
    cleaned_df['airline_icao'] = cleaned_df['airline_icao'].fillna('000')

    # Rename Columns
    cleaned_df = cleaned_df.rename(columns={
        'icao': 'icao_code',
        'iata': 'iata_code'
    })

    # Focus on essential columns (ignore structural noise columns)
    final_cols = [
        'hex', 'reg_number', 'icao_code', 'iata_code', 'model', 'manufacturer', 'airline_icao'
    ]
    dim_aircrafts = cleaned_df[final_cols].copy()

    # Deduplicate based on hex code
    dim_aircrafts = dim_aircrafts.drop_duplicates(subset=['hex'])

    print(f"Unique aircraft records for DIM_AIRCRAFT: {len(dim_aircrafts)}")

    return dim_aircrafts


# =========================================================================
# CLEAN /citiesDB -> DIM_CITIES
# =========================================================================

def clean_cities_db(df):
    """
    Cleans city data and formats it for the DIM_CITIES dimension table.
    """
    original_count = len(df)
    print(f"Original records from /citiesDB: {original_count}")

    cleaned_df = df.drop(columns=['type'], errors='ignore')

    # Rename columns to meet target database schema metrics
    rename_columns = {
        'name': 'city_name',
        'lat': 'latitude',
        'lng': 'longitude'
    }
    cleaned_df = cleaned_df.rename(columns=rename_columns)

    # Standardize country code upper-casing
    if 'country_code' in cleaned_df.columns:
        cleaned_df['country_code'] = cleaned_df['country_code'].str.upper()

    # Drop any record missing the PK (city_code), coordinates, or country_code
    critical_columns = ['city_code', 'latitude', 'longitude', 'country_code']
    cleaned_df = cleaned_df.dropna(subset=critical_columns)

    print(f"Records after dropping NaNs: {len(cleaned_df)}")

    # Deduplicate on the primary key column
    dim_cities = cleaned_df.drop_duplicates(subset=['city_code']).copy()

    print(f"Unique cities for DIM_CITIES: {len(dim_cities)}")

    return dim_cities


# =========================================================================
# CLEAN /countriesDB -> DIM_COUNTRIES
# =========================================================================

def clean_countries_db(df):
    """
    Cleans country data and formats it for the DIM_COUNTRIES dimension table.
    """
    original_count = len(df)
    print(f"Original records from /countries: {original_count}")

    cleaned_df = df.copy()

    # Rename columns to meet target database schema metrics
    rename_columns = {
        'code': 'country_code_2',   # PK
        'code3': 'country_code_3',
        'name': 'country_name'
    }
    cleaned_df = cleaned_df.rename(columns=rename_columns)

    # Drop rows missing the primary key or critical name fields
    cleaned_df = cleaned_df.dropna(subset=['country_code_2', 'country_name'])

    # Deduplicate on the primary key column
    cleaned_df = cleaned_df.drop_duplicates(subset=['country_code_2'])

    # Standardize primary key string to upper-casing
    cleaned_df['country_code_2'] = cleaned_df['country_code_2'].str.upper()

    if 'country_code_3' in cleaned_df.columns:
        cleaned_df['country_code_3'] = cleaned_df['country_code_3'].str.upper()

    print(f"Unique countries for DIM_COUNTRIES: {len(cleaned_df)}")

    return cleaned_df


###########
# DIM_TIME ?
###########
def clean_time_db(df_flights):
    """
    Extracts timestamps from real-time flight telemetry to generate a unique DIM_TIME dimension table.
    :param: DataFrame
    """

###########
# MISSING REQUEST FROM ENDPOINT 'schedule' to append schedule info to fact_flights
###########


# =========================================================================
# CLEAN /flights -> FACT_FLIGHTS & DIM_FLIGHT_POSITION
# =========================================================================

def clean_flights(df_flights):
    """
    Cleans real-time flights data and creates two separate connected DataFrames:
    1. fact_flights (parent)
    2. dim_flight_position (child via flight_id FK relationship)
    3. df_live_aircraft_patch (extracted aircraft metadata for dim_aircrafts enrichment)
    """
    original_count = len(df_flights)
    print(f"Original records from /flights: {original_count}")

    cleaned_df = df_flights.copy()

    # Generate time_key from UNIX timestamp safely
    if 'updated' in cleaned_df.columns:
        cleaned_df['time_key'] = pd.to_datetime(cleaned_df['updated'], unit='s').dt.strftime('%Y%m%d_%H%M')
    else:
        cleaned_df['time_key'] = 'UNKNOWN_TIME'

    # Drop low-density telemetry columns to remove structural noise early
    columns_to_drop = ['squawk', 'v_speed', 'updated']
    cleaned_df = cleaned_df.drop(columns=columns_to_drop, errors='ignore')

    # Rename columns to meet target database schema metrics
    rename_columns = {
        'hex': 'aircraft_hex',
        'dep_icao': 'origin_airport_id',
        'arr_icao': 'dest_airport_id',
        'lat': 'aircraft_latitude',
        'lng': 'aircraft_longitude',
        'alt': 'aircraft_altitude',
        'dir': 'aircraft_heading',
        'speed': 'aircraft_speed'
    }
    cleaned_df = cleaned_df.rename(columns=rename_columns)

    # Clean index and generate Sequential Integer Primary Key
    cleaned_df = cleaned_df.reset_index(drop=True)
    cleaned_df['flight_id'] = cleaned_df.index + 1

    # Extract parent table fact_flights
    fact_cols = [
        'flight_id',
        'flight_number', # 'movement_type',
        # 'flight_iata', 'flight_icao',
        'status',
        # 'duration', 'delayed'
        'origin_airport_id',
        'dest_airport_id',
        'airline_icao',
        # 'airline_iata',
        'aircraft_hex',
        'time_key',
        # scheduled_dep_time TIMESTAMP,
        # actual_dep_time TIMESTAMP,
        # scheduled_arr_time TIMESTAMP,
        # actual_arr_time TIMESTAMP,
    ]
    fact_flights = cleaned_df[fact_cols].copy()

    # Extract child table dim_flight_position
    position_cols = [
        'flight_id',
        'aircraft_latitude',
        'aircraft_longitude',
        'aircraft_altitude',
        'aircraft_heading',
        'aircraft_speed'
    ]
    dim_flight_position = cleaned_df[position_cols].copy()

    # Extract Live Aircraft Data, to enrich dim_aircraft later on
    aircraft_patch_cols = ['aircraft_hex', 'reg_number', 'aircraft_icao']
    if all(col in cleaned_df.columns for col in aircraft_patch_cols):
        df_live_aircraft_patch = cleaned_df[aircraft_patch_cols].drop_duplicates(subset=['aircraft_hex']).copy()
        df_live_aircraft_patch['reg_number'] = df_live_aircraft_patch['reg_number'].fillna('UNKNOWN_REG')
    else:
        df_live_aircraft_patch = pd.DataFrame()

    print(f"Processed {original_count} raw movements into FACT_FLIGHTS and DIM_FLIGHT_POSITION, and Live Aircraft Patch.")

    return fact_flights, dim_flight_position, df_live_aircraft_patch



### TBD

# def enrich_dim_aircraft(dim_aircraft, df_live_aircraft_patch):
# def enrich_airlines_from_flights(dim_airlines, fact_flights):
# def enrich_airlines_from_flights(df_airlines, df_flights):