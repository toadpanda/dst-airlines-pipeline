import os
import config
import requests
import pandas as pd


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