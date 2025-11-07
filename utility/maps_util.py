import requests
import urllib.parse


def get_geo_data(address: str) -> str:
    """
    Convert a delivery address into a URL-safe format
    that Google Geocoding API accepts.
    """
    if not address:
        raise ValueError("Address cannot be empty")
    
    # Strip leading/trailing spaces and encode for URL
    geo_response = {}
    formatted_address = urllib.parse.quote_plus(address.strip())
    
    geocodeapi_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={formatted_address}&key={APIKEY}"
    response = requests.get(geocodeapi_url)
    if response.status_code != 200:
        raise ValueError("Failed to fetch geocoding data")
    postal_code = response.json()["results"][0]["address_components"][-1]["long_name"] if response.json()["results"][0]["address_components"][-1]["types"][0] == "postal_code" else None
    country = response.json()["results"][0]["address_components"][-2]["long_name"] if response.json()["results"][0]["address_components"][-2]["types"][0] == "country" else None
    country_code = response.json()["results"][0]["address_components"][-2]["short_name"] if response.json()["results"][0]["address_components"][-2]["types"][0] == "country" else None
    print(response.json())
    response = response.json()["results"][0]
    geo_response = response["geometry"]["location"]
    geo_response["place_id"] = response["place_id"]
    geo_response["formatted_address"] = response["formatted_address"]
    geo_response["country"] = country
    geo_response["country_code"] = country_code
    geo_response["postal_code"] = postal_code
    print(geo_response)
    return geo_response



# 13.0382091 80.1544041
# 13.0382091 80.1544041