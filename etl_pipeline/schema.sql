-- Reset

DROP TABLE IF EXISTS dim_country;
DROP TABLE IF EXISTS dim_city;
DROP TABLE IF EXISTS dim_airport;
DROP TABLE IF EXISTS dim_aircraft;
DROP TABLE IF EXISTS dim_airline;
DROP TABLE IF EXISTS dim_time;
DROP TABLE IF EXISTS dim_flight_position;
DROP TABLE IF EXISTS fact_flight;

-- =====================================
-- Create DIMENSION Tables
-- =====================================

CREATE TABLE dim_country (
    country_code_2 CHAR(2) PRIMARY KEY, -- code2 = industry standard
    country_code_3 CHAR(3) UNIQUE NOT NULL,
    country_name VARCHAR(100) NOT NULL
);

CREATE TABLE dim_city (
    city_code CHAR(3) PRIMARY KEY,
    city_name VARCHAR(100) NOT NULL,
    latitude DECIMAL(9,6),
    longitude DECIMAL (9,6),
    country_code CHAR(2),
    FOREIGN KEY (country_code) REFERENCES dim_country(country_code_2)
);

CREATE TABLE dim_airport (
    airport_id SERIAL PRIMARY KEY, -- Surrogate ID (Auto-increment ???)
    airport_name VARCHAR(255) NOT NULL,
    iata_code CHAR(3),
    icao_code CHAR(4) UNIQUE NOT NULL,
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    country_code CHAR(2),
    FOREIGN KEY (country_code) REFERENCES dim_countries(country_code_2)
);
-- surrogate ID (auto-increment): when pushing DF to the DB (to_sql()), do not include airport_id column.
-- The column is defined as SERIAL, the database will automatically assign the ID to each row as it arrives (counting upwards from 1)

CREATE TABLE dim_aircraft (
    hex CHAR(6) PRIMARY KEY, -- transponder hex code; unique, hardware-level id for an aircraft
    reg_number VARCHAR(10) UNIQUE,
    icao_code CHAR(4),
    iata_code CHAR(3),
    model VARCHAR(100),
    manufacturer VARCHAR(100),
    airline_icao CHAR(3),
    FOREIGN KEY (airline_icao) REFERENCES dim_airline(airline_icao)
);

CREATE TABLE dim_airline (
    icao_code CHAR(3) PRIMARY KEY,
    iata_code CHAR(3),
    airline_name VARCHAR(255) NOT NULL,
    country_code CHAR(2), -- 'flag' from the flight endpoint
    FOREIGN KEY (country_code) REFERENCES dim_country(country_code_2)
);

CREATE TABLE dim_time (
    time_key INT PRIMARY KEY, -- Formatted as YYYYMMDDHHMM
    flight_timestamp TIMESTAMP NOT NULL,
    date_part DATE NOT NULL,
    hour_part INT NOT NULL,
    minute_part INT NOT NULL,
    day_of_week VARCHAR(10) NOT NULL,
    is_weekend INT NOT NULL -- 1 for True, 0 for False
);

CREATE TABLE dim_flight_position (
    position_key SERIAL PRIMARY KEY, -- Surrogate ID
    flight_id INT,
    aircraft_altitude INT,
    aircraft_latitude DECIMAL(9,6),
    aircraft_longitude DECIMAL(9,6),
    aircraft_heading INT,
    aircraft_speed INT,
    FOREIGN KEY (flight_id) REFERENCES fact_flight(flight_id)
);

-- =====================================
-- Create FACT Table
-- =====================================

CREATE TABLE fact_flight (
    flight_id INTEGER PRIMARY KEY, -- Sequential Integer
    flight_number VARCHAR(10),
    movement_type VARCHAR(10), -- 'departure' or 'arrival' / or 'global'?
    status VARCHAR(20),
    dep_delayed_min DECIMAL(5,2), -- drop and create in PowerBI later?
    arr_delayed_min DECIMAL(5,2), -- drop and create in PowerBI later?
    time_key INT,
    origin_airport_id INT,
    dest_airport_id INT,
    airline_icao CHAR(3),
    aircraft_hex CHAR(6),
    scheduled_dep_time TIMESTAMP,
    actual_dep_time TIMESTAMP,
    scheduled_arr_time TIMESTAMP,
    actual_arr_time TIMESTAMP,

    FOREIGN KEY (time_key) REFERENCES dim_time(time_key),
    FOREIGN KEY (origin_airport_id) REFERENCES dim_airport(airport_id),
    FOREIGN KEY (dest_airport_id) REFERENCES dim_airport(airport_id),
    FOREIGN KEY (airline_icao) REFERENCES dim_airline(icao_code),
    FOREIGN KEY (aircraft_hex) REFERENCES dim_aircraft(hex)
);