import json
import requests
from pathlib import Path

from . import config


# ==========================================
# Data retrieval functions
# ==========================================

def get_local_files():
    """Yield each FHIR bundle (parsed JSON) found in the local folder."""
    folder = Path(config.LOCAL_FOLDER)
    if not folder.exists():
        print(f"❌ Local folder {config.LOCAL_FOLDER} does not exist.")
        return
    for file_path in folder.glob("*.json"):
        try:
            with open(file_path, 'r') as f:
                yield json.load(f)
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")

def get_api_data():
    """Yield each FHIR bundle (page of results) fetched from the API,
    paging through up to max_pages per resource type."""
    for resource_type in config.RESOURCE_TABLE_MAP.keys():
        url = f"{config.FHIR_API_URL}/{resource_type}"
        params = {"_count": "50"}
        pages_fetched = 0
        max_pages = 3

        while url and pages_fetched < max_pages:
            try:
                if pages_fetched == 0:
                    response = requests.get(url, params=params)
                else:
                    response = requests.get(url)

                if response.status_code == 200:
                    data = response.json()
                    yield data
                    links = data.get("link", [])
                    next_link = next((link['url'] for link in links if link.get('relation') == 'next'), None)
                    url = next_link
                    pages_fetched += 1
                else:
                    print(f"❌ API Error fetching {resource_type}: {response.status_code} - {response.text}")
                    break
            except Exception as e:
                print(f"❌ Request failed for {resource_type}: {e}")
                break