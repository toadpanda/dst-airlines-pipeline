import os
import config
import requests
import pandas as pd
from datetime import datetime


def ingest_flight_data(endpoint_key, params=None, cache_name=None, verbose=True):
    """
    Fetches raw data from the AirLabs API, optionally caches it, and returns a DataFrame.

    Args:
        endpoint_key (str): The key mapping to the API path defined in config.py (e.g.: 'flights').
        params (dict, optional): Query parameters to filter the API request (e.g.: {'dep_iata': 'LHR'}).
            Defaults to None.
        cache_name (str, optional): The filename (without extension) to save the raw JSON response
            as a CSV in 'data/raw'. If None, no caching occurs.
        verbose (bool, optional): If True, prints schema info and request status for debugging.
            Defaults to True.

    Returns:
        pd.DataFrame: A DataFrame containing the raw API response, or None if the request failed.
    """
    ### Fetching ###
    # Get the path from the mapping and construct URL
    path = config.ENDPOINTS.get(endpoint_key)
    if not path:
        raise ValueError(f"Endpoint '{endpoint_key}' not defined.")

    url = f"{config.BASE_URL}/{path}"

    # Add API key to params automatically
    params = params or {}
    params['api_key'] = config.AIRLABS_API_KEY

    # Make request
    response = requests.get(url, params=params)
    data = response.json()

    ### Safety Check ###
    if 'response' not in data:
        print(f"Error: No valid data returned. API Message: {data.get('error', 'Unknown error')}")
        return None

    ### Convert to DataFram ###
    df = pd.DataFrame(data['response'])

    ### Optional Cache ###
    if cache_name:
        # Get the directory of the file that contains this function (api_utils.py)
        # This assumes api_utils.py is at the root.
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Define the path relative to the root
        output_dir = os.path.join(script_dir, 'data', 'raw')

        # Create the folder safely
        os.makedirs(output_dir, exist_ok=True)

        # Construct the file path
        file_path = os.path.join(output_dir, f"{cache_name}.csv")

        df.to_csv(file_path, index=False)
        if verbose:
            print(f"--- Cached raw data to {file_path} ---")

    ### Optional Inspection ###
    if verbose:
        print(f"--- Data Schema Overview for '{endpoint_key}' ---")
        print(f"Status Code: {response.status_code}")
        print(df.info())
        print(f"Columns: {df.columns.tolist()}")

    return df


def run_batch_ingestion(ingestion_plan, verbose=True):
    """
    Loops through a specified list of endpoints, fetches the raw data,
    and applies endpoint-specific parameters.

    Args:
        ingestion_plan (dict): A dictionary where keys are endpoint names (str)
                               and values are dictionaries of parameters (dict)
                               to pass to the API request.
        verbose (bool): If True, prints status messages. Defaults to True.

    Returns:
        dict: A dictionary containing the fetched DataFrames, keyed by endpoint.
    """
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H")
    print(f"Starting Batch Ingestion at {timestamp}...")

    all_dataframes = {}

    for endpoint, params in ingestion_plan.items():
        try:
            # Use timestamp in the cache_name for versioned files
            cache_name = f"raw_{endpoint}_{timestamp}"

            # Pass the specific params for this endpoint
            df = ingest_flight_data(endpoint, params=params, cache_name=cache_name, verbose=verbose)
            all_dataframes[endpoint] = df
            print(f"Successfully ingested {endpoint}")
        except Exception as e:
            print(f"Failed to ingest {endpoint}: {e}")

    return all_dataframes


def get_data(endpoint_key, params=None):
    if params is None:
        params = {}

    # Get the path from the mapping
    path = config.ENDPOINTS.get(endpoint_key)
    if not path:
        raise ValueError(f"Endpoint '{endpoint_key}' not defined.")

    # Construct the URL
    url = f"{config.BASE_URL}{path}"

    # Add API key to params automatically
    params['api_key'] = config.AIRLABS_API_KEY

    response = requests.get(url, params=params)

    # Return JSON if successful, or the error text for debugging
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.status_code, "message": response.text}


def inspect_endpoint_data(data, cache_name=None):
    """
    Takes the raw JASON response from any AirLabs endpoint, displays a structural summary (DataFrame), and optionally caches it to a local CSV file.
    """
    if not data or 'response' not in data:
        print("No valid response data found.")
        return None

    # Extract the list of records
    records = data['response']

    if len(records) == 0:
        print("The response list is empty.")
        return None

    # Convert to DataFrame
    df = pd.DataFrame(records)

    # Print schema information
    print("--- Data Schema Overview ---")
    print(df.info())

    # Optional Automated CSV Caching
    if cache_name:
        data_dir = os.path.join(config.BASE_DIR, 'data')
        os.makedirs(data_dir, exist_ok=True)

        file_path = os.path.join(data_dir, f"{cache_name}.csv")
        df.to_csv(file_path, index=False)
        print(f"Success: Data cached locally to '{file_path}'.")

    # Return the full DataFrame
    return df