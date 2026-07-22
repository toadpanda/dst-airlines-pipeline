# DST Airlines Data Pipeline
An automated ETL and data processing pipeline designed to ingest, clean and structure aviation datasets into a clean star schema relational database format using the AirLabs API.

## Contributors & Architecture Ownership
This repository houses the core Data Engineering ingestion pipeline and exploratory data analysis sandbox for our group project. 

* **Pipeline Architect & Core Developer:** Leoni Gilke
  * Designed, implemented, and authored the entire codebase currently hosted in this repository, including the ETL pipeline utilities (`pipeline_utils.py`), API wrappers (`api_utils.py`), and configuration frameworks (`config.py`).
* **Project Team:** Rustam U.
  * Collaborating on project conceptualization, analytical reporting, and downstream dashboard development.

---

## Project Goal
An educational data engineering initiative to build an automated ingestion pipeline for real-time airline operations data using the AirLabs API, transforming raw telemetry into an optimized relational Star Schema.

---

## Evaluation of Data Sources
Our team evaluated several flight data providers—including **OpenSky** and **Aviationstack**—before selecting **AirLabs** for our data pipeline based on three key factors:
* **Data Suitability:** AirLabs provides the specific granularity required, including flight numbers, real-time status updates, and aircraft type details.
* **Budget-Friendly Constraints:** The free-tier allowance of 1,000 requests per month is ideal for our academic development lifecycle.
* **Ease of Implementation:** Highly accessible documentation allowing fast authentication and data extraction.

---

## Data-Driven Modeling Methodology
To ensure optimal storage efficiency and data integrity, data types and column constraints are aligned with the operational requirements of our downstream database schema, ensuring the pipeline handles real-world variability cleanly.

---

## Workflow Pipeline ('ELT' Architecture)
Our pipeline follows an **ELT (Extract, Load, Transform)** architecture designed for scalability and analytical readiness:

1. **Extraction (`api_utils.py`):** Handles communication protocols, session handlers, and endpoint requests with built-in API quota protection.
2. **Transformation (`pipeline_utils.py`):** Cleans data, standardizes naming conventions, backfills missing attributes, and structures information into Fact and Dimension tables.
3. **Loading:** Persists cleaned data into a relational database powering our analytical reporting layers.

---

## Repository Structure

```text
dst-airlines-pipeline/
│
├── deliverables/
│   └── Report_1.md             # Project report and initial analytical findings
├── samples/
│   └── flights_sample.json     # Sample raw JSON response payload from flight endpoints
├── .gitignore                  # Git exclusion rules (caches, virtual environments, local configs)
├── api_utils.py                # Core utilities for handling API connections and requests
├── config.py                   # Centralized configuration parameters and environment keys
└── pipeline_utils.py           # Core ETL transformation and data cleaning utility functions
   
```

---

## Setup & Configuration
1. Obtain an API key from [AirLabs](https://airlabs.co).
2. Create a `.env` file in the root directory:
   `AIRLABS_API_KEY=your_key_here`
3. **Execute ingestion or pipeline scripts:** Use your notebook environment or custom scripts to invoke `api_utils.py` and `pipeline_utils.py` for data processing.

---

## Data Sample
The following JSON structure demonstrates the data captured from the `flights` endpoint:
```json
{
    "hex": "347645",
    "reg_number": "EC-OEA",
    "flag": "ES",
    "lat": 34.810714,
    "lng": -4.78554,
    "alt": 11602,
    "dir": 51,
    "speed": 871,
    "v_speed": 0,
    "flight_number": "5772",
    "flight_icao": "IBB5772",
    "flight_iata": "NT5772",
    "dep_icao": "GCLP",
    "dep_iata": "LPA",
    "arr_icao": "LEAM",
    "arr_iata": "LEI",
    "airline_icao": "IBB",
    "airline_iata": "NT",
    "aircraft_icao": "E295",
    "updated": 1783179416,
    "status": "en-route",
    "type": "adsb"
}
```

---

##  Data Pipeline Utilities
The `pipeline_utils.py` module contains the core ETL (Extract, Transform, Load) transformation logic for cleaning raw API responses and structuring them into a star schema relational database format.

### Key Functions & Transformations:
* **`clean_airlines_db(df)`**: Processes raw airline data, filters for valid ICAO primary keys, standardizes missing IATA codes with `'000'`, and maps fields to target `dim_airlines` schema requirements.
* **`clean_airports_db(df)`**: Cleans airport records by ensuring mandatory coordinate data (`lat`, `lng`) and ICAO keys exist, while normalizing missing IATA codes.
* **`clean_aircraft_db(df)`**: Formats fleet metadata for `dim_aircrafts`, dropping unidentifiable records lacking a hex code and safely backfilling missing registrations with `'UNKNOWN_REG'`.
* **`clean_cities_db(df)` & `clean_countries_db(df)`**: Standardize geographical references, enforce uppercase formatting for country codes, and eliminate duplicates based on primary identifiers.
* **`clean_flights(df_flights)`**: 
  * Parses raw real-time flight telemetry, safely generating a `time_key` from UNIX timestamps.
  * Generates sequential integer primary keys (`flight_id`) to maintain a strict relational link between the parent **`fact_flights`** table and the child **`dim_flight_position`** telemetry table.
  * Extracts a live aircraft metadata patch (`df_live_aircraft_patch`) to allow iterative dynamic enrichment of the aircraft dimension table downstream.

---

## Development & API Limit Management

I am utilizing the AirLabs free-tier API, which enforces a strict limit of **1,000 requests per month**. To protect the quota during development, I implemented a local caching architecture:

1. **Ingest & Cache:** Live data is fetched once and passed to the core processing utility:
   ```python
   df_lh = inspect_endpoint_data(analytics_data, cache_name="lh_fleet")
   ```
   
