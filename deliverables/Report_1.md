# Data Engineering Project: Airline Pipeline Analysis
## Step 1: Exploration of Unstructured Data Report

**Group Members:** Leoni GILKE, Rustam U.   
**Submission Date:** June 26, 2026  
**Course:** ETL Intermediate (AE) Bootcamp — Jun26 (Mar26) English

---

## 1. Project Context & Scope

### 1.1 Source Selection Justification
For this data engineering project, our team evaluated several unstructured and semi-structured aviation data providers suggested in the project guidelines (Aviationstack, OpenSky Network, and AirLabs). After an initial sandbox testing phase, we decided to utilize the **AirLabs API** as our core data source for the following tactical reasons:
* **Aviationstack Constraints:** The free-tier account enforces a strict 100-request per month limit, which is too restrictive for continuous data pipeline development, local debugging, and iterative system integration.
* **OpenSky Network Constraints:** OpenSky predominantly focuses on raw academic tracker/telemetry streams, lacking embedded commercial operational metadata like real-time flight delays, schedule updates, or unified airport metadata maps.
* **AirLabs Advantage:** AirLabs offers an optimal balance for a data engineering architecture, allowing higher baseline testing flexibility alongside highly structured nested JSON payloads containing operational variables vital to generating realistic dashboards.

### 1.2 Definition of Project Scope
To maintain a realistic database scale on an analytical free-tier infrastructure, tracking the global aviation grid is impossible due to payload pagination constraints and query response timeouts. Consequently, our system architecture scales down processing workloads to a defined high-density geographic hub:

* **Target Constraints:** Tracking real-time incoming and outgoing air traffic routed through **London Heathrow Airport (IATA Code: LHR)** or flights operated via **British Airways (IATA Code: BA)**. 
* **Core Pipeline Objective:** Ingesting live spatial telemetry (`lat`, `lng`), time profiles, and scheduling markers to isolate structural delay patterns and flight status shifts during peak hours at Europe's highest-volume international transit hub.

### 1.3 Exploratory Environment Layout
The foundational extraction code has been abstracted into modular utility architecture within the repository:
* Core operational variables and target endpoints are centralized in `config.py`.
* The sanitized connection handler is hosted in `api_utils.py`.
* Live data exploration and payload calculations can be reviewed in the interactive notebook located at `notebooks/step_1_exploration.ipynb`.
* A raw, unedited sample payload from our exploratory fetches can be accessed directly at `deliverables/flights_sample.json`.

### 1.4 Architectural Assumptions & Code Constraints
To optimize execution and preserve configuration clarity, our pipeline bypasses inline string 
normalization methods (such as `.strip()`). Instead, the team enforces a strict configuration 
contract within `config.py` to ensure that raw f-string concatenation creates valid paths:
* `BASE_URL` is explicitly formatted with a trailing forward slash (`https://airlabs.co/api/v9/`).
* All mapping values inside the `ENDPOINTS` dictionary must omit a leading forward slash (e.g., `'flights': 'flights'`).

This configuration rule guarantees that `f"{config.BASE_URL}{endpoint}"` evaluates cleanly into 
the valid production target (`https://airlabs.co/api/v9/flights`) without risking double slashes or connection errors.

## 2. Data Ingestion Architecture & Framework

### 2.1 Technical Pipeline Isolation
To prevent configuration vulnerabilities and credential leaks in shared repositories, the pipeline implements a decoupled "Single Source of Truth" pattern. Secret authorization parameters are stored inside a local environment file (`.env`) that is explicitly blocked by our `.gitignore` policy. 

Upon runtime execution, `config.py` initiates the `load_dotenv()` mechanism once to bind variables to the local machine space. Reusable network calls are completely isolated within `api_utils.py` under the function `get_data(endpoint, params)`. This ensures that downstream analysis files remain decoupled from base connection mechanics.


## Section 3: Data Exploration and Quality Assessment

### 3.1 Structural Overview of Staging Dataset
To establish a foundation for tracking live flight transactions at London Heathrow (LHR), live telemetry and operational schedules were extracted via the AirLabs flights API endpoint. Payloads for arriving (`arr_iata=LHR`) and departing (`dep_iata=LHR`) traffic were ingested, programmatically tagged with a custom tracking field (`movement_type`), and merged into a single comprehensive staging DataFrame.

Given Heathrow's prominent position as a primary European mega-hub, the combined landing and takeoff sets yield an expanded master dataset comprising **194 initial rows** across **24 data columns**:

```text
<class 'pandas.DataFrame'>
RangeIndex: 194 entries, 0 to 193
Data columns (total 24 columns):
 #   Column         Non-Null Count  Dtype  
---  ------         --------------  -----  
 0   hex            194 non-null    str    
 1   reg_number     122 non-null    str    
 2   flag           194 non-null    str    
 3   lat            194 non-null    float64
 4   lng            194 non-null    float64
 5   alt            181 non-null    float64
 6   dir            192 non-null    float64
 7   speed          183 non-null    float64
 8   v_speed        78 non-null     float64
 9   flight_number  194 non-null    int64  
 10  flight_icao    194 non-null    str    
 11  flight_iata    193 non-null    str    
 12  dep_icao       194 non-null    str    
 13  dep_iata       194 non-null    str    
 14  arr_icao       194 non-null    str    
 15  arr_iata       194 non-null    str    
 16  airline_icao   194 non-null    str    
 17  airline_iata   194 non-null    str    
 18  aircraft_icao  194 non-null    str    
 19  updated        194 non-null    int64  
 20  status         194 non-null    str    
 21  type           194 non-null    str    
 22  squawk         2 non-null      float64
 23  movement_type  194 non-null    str    
dtypes: float64(7), int64(2), str(15)
```
*(Note: Total row counts fluctuate dynamically depending on the hour of live API call execution; these numbers represent a baseline peak-hour snapshot for modeling constraints).*


### 3.2 Data Density & Relational Integrity Check
An inspection of the field population rates confirms excellent data density for structural business keys, ensuring relational modeling is feasible:

* **100% Relational Density:** High-priority identification codes—including `flight_number`, `dep_iata` (origin), `arr_iata` (destination), `airline_iata` (carrier), and `aircraft_icao` (aircraft type)—contain zero missing values across all 194 rows. This structural integrity guarantees that our future Star Schema or 3NF structures can reliably map foreign keys without risking pipeline failures due to orphan keys.
* **Tracking Consistency:** The engineered `movement_type` attribute contains 194 non-null elements, validating that the ingestion layer accurately preserved the context of the flight directional flow during the merge phase.

---

### 3.3 Data Cleaning & Mitigation Strategy
Our analysis exposed specific data fields with low population density that require clear data engineering design decisions prior to warehouse mapping:

| Field | Population | Density | Strategy |
| :--- | :--- | :--- | :--- |
| `squawk` | 2/194 | <1% | **Drop:** Extremely sparse; lacks analytical significance. |
| `v_speed` | 78/194 | ~40.2% | **Omit:** Insufficient telemetry to support accurate dashboards. |
| `reg_number` | 122/194 | ~62.8% | **Impute:** Use `fleetsDB` reference lookup, fallback to `'UNKNOWN_REG'`. |
| `alt` & `speed` | >93% | >93% | **Clean:** Apply forward-filling or baseline default constraints. |_
