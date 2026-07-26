-- Reset

DROP TABLE IF EXISTS dim_country;
DROP TABLE IF EXISTS dim_city;
DROP TABLE IF EXISTS dim_airport;
DROP TABLE IF EXISTS dim_aircraft;
DROP TABLE IF EXISTS dim_airline;
DROP TABLE IF EXISTS dim_date;
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
    icao_code CHAR(4) PRIMARY KEY,
    iata_code CHAR(3),
    airport_name VARCHAR(255),
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    country_code CHAR(2),
    FOREIGN KEY (country_code) REFERENCES dim_country(country_code_2)
);
-- The column is defined as SERIAL, the database will automatically assign the ID to each row as it arrives (counting upwards from 1)

CREATE TABLE dim_aircraft (
    hex CHAR(6) PRIMARY KEY, -- transponder hex code; unique, hardware-level id for an aircraft
    reg_number VARCHAR(10),
    icao_code CHAR(4),
    iata_code CHAR(3),
    model VARCHAR(100),
    manufacturer VARCHAR(100),
    airline_icao CHAR(3),
    FOREIGN KEY (airline_icao) REFERENCES dim_airline(icao_code)
);

CREATE TABLE dim_airline (
    icao_code CHAR(3) PRIMARY KEY,
    iata_code CHAR(3),
    airline_name VARCHAR(255) NOT NULL,
    country_code CHAR(2), -- 'flag' from the flight endpoint
    FOREIGN KEY (country_code) REFERENCES dim_country(country_code_2)
);

CREATE TABLE dim_date (
    date_key INT PRIMARY KEY,
    full_date DATE NOT NULL,
    year INT NOT NULL,
    quarter INT NOT NULL,
    month INT NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    day_of_month INT NOT NULL,
    day_of_week INT NOT NULL,
    day_name VARCHAR(20) NOT NULL,
    day_of_year INT NOT NULL,
    is_weekend BOOLEAN NOT NULL,
    is_month_start BOOLEAN NOT NULL,
    is_month_end BOOLEAN NOT NULL
);

CREATE TABLE dim_time (
    time_key INT PRIMARY KEY, -- Formatted as HHMM
    time_string TIME NOT NULL,
    hour_24 INT NOT NULL,
    hour_12 INT NOT NULL,
    minute INT NOT NULL,
    am_pm CHAR(2) NOT NULL,
    shift VARCHAR(20) NOT NULL
);

CREATE TABLE dim_flight_position (
    position_key VARCHAR(100) PRIMARY KEY, -- Smart key
    flight_id VARCHAR(50),
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
    flight_id VARCHAR(50) PRIMARY KEY, -- combination flight code + date
    flight_number VARCHAR(10),
    status VARCHAR(20),
    dep_delayed_min DECIMAL(5,2), -- drop and create in PowerBI later?
    arr_delayed_min DECIMAL(5,2), -- drop and create in PowerBI later?

    updated_date_key INT,
    updated_time_key INT,

    dep_icao CHAR(4),
    arr_icao CHAR(4),
    airline_icao CHAR(3),
    aircraft_hex CHAR(6),

    scheduled_dep_time TIMESTAMP,
    actual_dep_time TIMESTAMP,
    scheduled_arr_time TIMESTAMP,
    actual_arr_time TIMESTAMP,

    FOREIGN KEY (updated_date_key) REFERENCES dim_date(date_key),
    FOREIGN KEY (updated_time_key) REFERENCES dim_time(time_key),
    FOREIGN KEY (dep_icao) REFERENCES dim_airport(icao_code),
    FOREIGN KEY (arr_icao) REFERENCES dim_airport(icao_code),
    FOREIGN KEY (airline_icao) REFERENCES dim_airline(icao_code),
    FOREIGN KEY (aircraft_hex) REFERENCES dim_aircraft(hex)
);