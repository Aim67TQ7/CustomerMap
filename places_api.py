
import googlemaps
from typing import Dict, List, Optional
import streamlit as st

@st.cache_resource
def get_gmaps_client():
    """Initialize Google Maps client with API key from secrets."""
    return googlemaps.Client(key=st.secrets["GOOGLE_MAPS_API_KEY"])

def geocode_address(address: str) -> Optional[Dict[str, float]]:
    """Geocode an address to get coordinates."""
    gmaps = get_gmaps_client()
    try:
        geocode_result = gmaps.geocode(address)
        if geocode_result:
            location = geocode_result[0]['geometry']['location']
            return {'lat': location['lat'], 'lng': location['lng']}
        return None
    except Exception as e:
        st.error(f"Geocoding error: {str(e)}")
        return None

def fetch_nearby_manufacturers(location: Dict[str, float], radius_miles: float) -> List[Dict]:
    """Fetch nearby manufacturers within specified radius."""
    gmaps = get_gmaps_client()
    radius_meters = radius_miles * 1609.34  # Convert miles to meters
    
    manufacturers = []
    try:
        results = gmaps.places_nearby(
            location=location,
            radius=radius_meters,
            type='manufacturer'
        )
        
        # Process initial results
        manufacturers.extend(process_places_results(results.get('results', [])))
        
        # Handle pagination
        while 'next_page_token' in results:
            import time
            time.sleep(2)  # Required delay before using next_page_token
            results = gmaps.places_nearby(page_token=results['next_page_token'])
            manufacturers.extend(process_places_results(results.get('results', [])))
            
        return manufacturers
    except Exception as e:
        st.error(f"Error fetching places: {str(e)}")
        return []

def process_places_results(results: List[Dict]) -> List[Dict]:
    """Process and clean places results."""
    processed = []
    for place in results:
        # Get additional place details for each result
        try:
            gmaps = get_gmaps_client()
            details = gmaps.place(place['place_id'], fields=['formatted_phone_number', 'website'])['result']
        except:
            details = {}
            
        processed.append({
            'Name': place.get('name', 'N/A'),
            'Address': place.get('vicinity', 'N/A'),
            'Latitude': place['geometry']['location']['lat'],
            'Longitude': place['geometry']['location']['lng'],
            'Rating': place.get('rating', 'N/A'),
            'Phone': details.get('formatted_phone_number', 'N/A'),
            'Website': details.get('website', 'N/A')
        })
    return processed
