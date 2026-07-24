import pandas as pd


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


# =========================================================================
# CLEAN /SCHEDULES -> [FACT_FLIGHTS]
# =========================================================================

def clean_schedules(df):
    """
    Standardizes the raw schedules DataFrame before merging.
    :param df: raw df after extraction
    :return: df_clean
    """
    # Define the exact columns to keep
    columns_to_keep = [
        'flight_number',
        'flight_icao',
        'airline_icao',
        'dep_icao',
        'arr_icao',
        'dep_time_utc',
        'dep_actual_utc',
        'arr_time_utc',
        'arr_actual_utc',
        'status',
        'dep_delayed',
        'arr_delayed'
    ]

    # Filter to only keep existing columns
    existing_cols = [col for col in columns_to_keep if col in df.columns]
    df_clean = df[existing_cols].copy()

    # Convert time columns to standard datetime objects
    time_columns = ['dep_time_utc', 'dep_actual_utc', 'arr_time_utc', 'arr_actual_utc']
    for col in time_columns:
        if col in df_clean.columns:
            df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')

    # Rename to match fact_flight schema
    df_clean.rename(columns={
        'dep_time_utc': 'scheduled_dep_time',
        'dep_actual_utc': 'actual_dep_time',
        'arr_time_utc': 'scheduled_arr_time',
        'arr_actual_utc': 'actual_arr_time',
        'dep_delayed': 'dep_delayed_min',
        'arr_delayed': 'arr_delayed_min'
    }, inplace=True)

    return df_clean


# =========================================================================
# CLEAN / TRANSFORM -> DIM_DATE
# =========================================================================

def generate_dim_date(start_date='2026-01-01', end_date='2036-12-31'):
    """
    Generates a static dim_date table for a dimensional model.
    :param start_date: Start Date
    :param end_date: End Date
    :return: df[columns]
    """
    # Create a continuous range of dates
    df = pd.DataFrame({'full_date': pd.date_range(start_date, end_date)})

    # Create the primary key as an integer (YYYYMMDD)
    df['date_key'] = df['full_date'].dt.strftime('%Y%m%d').astype(int)

    # Extract standard calendar attributes
    df['year'] = df['full_date'].dt.year
    df['quarter'] = df['full_date'].dt.quarter
    df['month'] = df['full_date'].dt.month
    df['month_name'] = df['full_date'].dt.month_name()
    df['day_of_month'] = df['full_date'].dt.day
    df['day_of_week'] = df['full_date'].dt.dayofweek + 1  # Monday=1, Sunday=7
    df['day_name'] = df['full_date'].dt.day_name()
    df['day_of_year'] = df['full_date'].dt.dayofyear

    # Create boolean/flag columns (1 = True, 0 = False)
    df['is_weekend'] = df['full_date'].dt.dayofweek.isin([5, 6]).astype(int)
    df['is_month_start'] = df['full_date'].dt.is_month_start.astype(int)
    df['is_month_end'] = df['full_date'].dt.is_month_end.astype(int)

    # Reorder columns to put date_key first
    columns = ['date_key', 'full_date'] + [c for c in df.columns if c not in ['date_key', 'full_date']]

    return df[columns]


# =========================================================================
# CLEAN / TRANSFORM -> DIM_TIME
# =========================================================================
def generate_dim_time():
    """
    Generates a static dim_time table at the minute grain (1,440 rows).
    :returns: df[['time_key', 'time_string', 'hour_24', 'hour_12', 'minute', 'am_pm', 'shift']]
    """
    times = pd.date_range("00:00:00", "23:59:00", freq="min").time
    df = pd.DataFrame({'time_string': times})

    # Create integer key (e.g. 14:15 becomes 1415)
    df['time_key'] = df['time_string'].apply(lambda x: x.hour * 100 + x.minute)
    df['time_string'] = df['time_string'].astype(str)
    df['hour_24'] = pd.to_datetime(df['time_string'], format='%H:%M:%S').dt.hour
    df['hour_12'] = df['hour_24'].apply(lambda x: x % 12 or 12)
    df['minute'] = pd.to_datetime(df['time_string'], format='%H:%M:%S').dt.minute
    df['am_pm'] = df['hour_24'].apply(lambda x: 'AM' if x < 12 else 'PM')

    def get_shift(hour):
        if 5 <= hour < 12:
            return 'Morning'
        elif 12 <= hour < 17:
            return 'Afternoon'
        elif 17 <= hour < 22:
            return 'Evening'
        else:
            return 'Night'

    df['shift'] = df['hour_24'].apply(get_shift)

    return df[['time_key', 'time_string', 'hour_24', 'hour_12', 'minute', 'am_pm', 'shift']]


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

    # Generate dimensional date and time keys from UNIX timestamp safely
    if 'updated' in cleaned_df.columns:
        dt_obj = pd.to_datetime(cleaned_df['updated'], unit='s', errors='coerce')
        cleaned_df['updated_date_key'] = dt_obj.dt.strftime('%Y%m%d').astype(int)
        cleaned_df['updated_time_key'] = dt_obj.dt.hour * 100 + dt_obj.dt.minute
    else:
        cleaned_df['updated_date_key'] = 0
        cleaned_df['updated_time_key'] = 0

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

    # Clean index and generate a Smart Key
    base_id = cleaned_df['flight_icao'].fillna(cleaned_df['aircraft_hex']).astype(str)
    cleaned_df['flight_id'] = base_id + "_" + cleaned_df['updated_date_key'].astype(str)

    # Extract parent table fact_flights
    fact_cols = [
        'flight_id',
        'flight_number',
        'flight_iata',
        'flight_icao',
        'status',
        'origin_airport_id',
        'dest_airport_id',
        'airline_icao',
        'airline_iata',
        'aircraft_hex',

        'updated_date_key',
        'updated_time_key',
    ]
    # Ensure we only select columns that actually exist to prevent KeyErrors
    existing_fact_cols = [col for col in fact_cols if col in cleaned_df.columns]
    fact_flights = cleaned_df[existing_fact_cols].copy()

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


# =========================================================================
# BUILD FACT_FLIGHTS
# =========================================================================

def build_fact_flight(fact_flights, df_clean_schedules):
    """
    Merges cleaned live flights and cleaned schedules into the final fact table.
    """
    # Only keep the timing data from schedules
    cols_to_keep_from_schedules = [
        'flight_icao',  # Crucial for joining
        'scheduled_dep_time',
        'actual_dep_time',
        'scheduled_arr_time',
        'actual_arr_time',
        'dep_delayed_min',
        'arr_delayed_min'
    ]

    # Filter schedules to avoid _x and _y suffix conflicts during merge
    exist_cols = [c for c in cols_to_keep_from_schedules if c in df_clean_schedules.columns]
    df_sched_subset = df_clean_schedules[exist_cols]

    # Left join schedules onto live flights master dataframe
    final_fact_df = pd.merge(
        fact_flights,
        df_sched_subset,
        on='flight_icao',
        how='left'
    )

    # Final safety net: strictly filter the columns to match schema.sql exactly
    final_columns = [
        'flight_id',
        'flight_number',
        'movement_type',
        'status',
        'dep_delayed_min',
        'arr_delayed_min',
        'updated_date_key',
        'updated_time_key',
        'origin_airport_id',
        'dest_airport_id',
        'airline_icao',
        'aircraft_hex',
        'scheduled_dep_time',
        'actual_dep_time',
        'scheduled_arr_time',
        'actual_arr_time'
    ]

    existing_final_cols = [col for col in final_columns if col in final_fact_df.columns]

    return final_fact_df[existing_final_cols]


# =========================================================================
# LOAD NEW INCREMENTAL FLIGHTS
# =========================================================================

def load_incremental_flights(engine, fact_flights, dim_flight_position):
    """
    Loads flights using Python-generated Smart Keys.
    :param engine:
    :param fact_flights:
    :param dim_flight_position:
    :return:
    """
    # Check database which flight_ids already exist
    existing_ids_df = pd.read_sql("SELECT flight_id FROM fact_flight;", engine)
    existing_ids = existing_ids_df['flight_id'].tolist()

    # Filter fact_flight to only keep new, unseen flight_ids
    new_facts = fact_flights[~fact_flights['flight_id'].isin(existing_ids)]

    # Drop any duplicates that exist within the current API payload
    new_facts = new_facts.drop_duplicates(subset=['flight_id'])

    # Track metrics for the return statement
    added_flights_count = len(new_facts)
    added_telemetry_count = len(dim_flight_position)

    # Append the new flights to the database
    if not new_facts.empty:
        new_facts.to_sql('fact_flight', engine, if_exists='append', index=False)
        print(f"Added {len(new_facts)} new flights.")

    # Append all telemetry positions
    dim_flight_position.to_sql('dim_flight_position', engine, if_exists='append', index=False)
    print(f"Appended {len(dim_flight_position)} new telemetry points.")

    return added_flights_count, added_telemetry_count


# =========================================================================
# ENRICH DIM_AIRLINES & DIM_AIRCRAFTS
# =========================================================================

def enrich_dim_airlines(existing_airlines, raw_flights_df):
    """
    Updates dim_airline with missing IATA codes and country flags
    discovered in the live telemetry stream.
    :param existing_airlines:
    :param raw_flights_df:
    :return: existing_airlines
    """
    # Extract airline info from the raw flights payload
    # We use raw_flights_df because 'flag' and 'airline_iata' were dropped during clean_flights
    cols = ['airline_icao', 'airline_iata', 'flag']
    live_airlines = raw_flights_df[[c for c in cols if c in raw_flights_df.columns]].dropna(subset=['airline_icao'])

    # Deduplicate so we only have one row per airline
    live_airlines = live_airlines.drop_duplicates(subset=['airline_icao'])

    # Convert to dictionary for fast mapping
    iata_mapping = dict(zip(live_airlines['airline_icao'], live_airlines.get('airline_iata', pd.Series())))
    flag_mapping = dict(zip(live_airlines['airline_icao'], live_airlines.get('flag', pd.Series())))

    # Patch the existing dimensions
    # If iata_code is null or a placeholder like '000', overwrite it with live data
    needs_iata = existing_airlines['iata_code'].isnull() | (existing_airlines['iata_code'] == '000')
    existing_airlines.loc[needs_iata, 'iata_code'] = existing_airlines.loc[needs_iata, 'icao_code'].map(
        iata_mapping).fillna(existing_airlines['iata_code'])

    # If country_code (flag) is missing, overwrite it
    needs_flag = existing_airlines['country_code'].isnull()
    existing_airlines.loc[needs_flag, 'country_code'] = existing_airlines.loc[needs_flag, 'icao_code'].map(
        flag_mapping).fillna(existing_airlines['country_code'])

    # ================================================
    # Append new airlines missing from the database
    existing_icaos = set(existing_airlines['icao_code'].dropna())
    new_airlines = live_airlines[~live_airlines['airline_icao'].isin(existing_icaos)].copy()

    # If there are new airlines, format them and append
    if not new_airlines.empty:
        new_airlines = new_airlines.rename(columns={
            'airline_icao': 'icao_code',
            'airline_iata': 'iata_code',
            'flag': 'country_code'
        })
        new_airlines['airline_name'] = 'UNKNOWN_AIRLINE'

        # Align columns to match the existing DataFrame
        cols_to_keep = ['icao_code', 'iata_code', 'airline_name', 'country_code']
        new_airlines = new_airlines[[c for c in cols_to_keep if c in new_airlines.columns]]

        # Merge historical dim_airlines and new rows
        existing_airlines = pd.concat([existing_airlines, new_airlines], ignore_index=True)

    return existing_airlines


def enrich_dim_aircraft(dim_aircraft, df_live_aircraft_patch):
    """
    Enriches dim_aircraft by identifying new aircraft from live telemetry.
    Uses historical fleet data to fill missing registration numbers.

    :return: enriched_dim (full dataframe combining historical and new aircraft)
    """
    if df_live_aircraft_patch.empty:
        return dim_aircraft.copy()

    # Standardize the patch column name for the merge
    df_master = df_live_aircraft_patch.rename(columns={'aircraft_hex': 'hex'}).copy()

    # Extract reference keys from the existing dimension to create a lookup
    fleet_lookup = dim_aircraft[['hex', 'reg_number']].rename(columns={'reg_number': 'reg_from_fleet'})

    # Merge df_master with fleet_lookup on 'hex' using a left-join
    df_master = df_master.merge(fleet_lookup, on='hex', how='left')

    # Fill missing 'reg_number' in df_master with 'reg_from_fleet'
    df_master['reg_number'] = df_master['reg_number'].fillna(df_master['reg_from_fleet'])

    # Drop the temporary 'reg_from_fleet' column
    df_master = df_master.drop(columns=['reg_from_fleet'])

    # Fill any remaining unmapped Null values in 'reg_number' with 'UNKNOWN_REG'
    df_master['reg_number'] = df_master['reg_number'].fillna('UNKNOWN_REG')

    # Identify completely new aircraft missing from dim_aircraft
    existing_hexes = set(dim_aircraft['hex'].dropna())
    new_rows = df_master[~df_master['hex'].isin(existing_hexes)].copy()

    # Combine the historical dim_aircraft with the new rows
    if not new_rows.empty:
        # Rename to match the database schema
        if 'aircraft_icao' in new_rows.columns:
            new_rows = new_rows.rename(columns={'aircraft_icao': 'icao_code'})

        # Ensure fallback values for missing schema columns
        if 'iata_code' not in new_rows.columns:
            new_rows['iata_code'] = '000'
        if 'airline_icao' not in new_rows.columns:
            new_rows['airline_icao'] = '000'

        # Select only valid schema columns to prevent SQLAlchemy crashes
        valid_schema_cols = ['hex', 'reg_number', 'icao_code', 'iata_code', 'model', 'manufacturer', 'airline_icao']
        new_rows = new_rows[[c for c in valid_schema_cols if c in new_rows.columns]]

        enriched_dim = pd.concat([dim_aircraft, new_rows], ignore_index=True)
    else:
        enriched_dim = dim_aircraft.copy()

    # Clean up duplicates based on hex
    enriched_dim = enriched_dim.drop_duplicates(subset=['hex']).reset_index(drop=True)

    return enriched_dim

