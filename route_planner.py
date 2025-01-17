
import streamlit as st
from typing import List, Dict
import folium
from streamlit_folium import folium_static
from itertools import permutations
from math import radians, sin, cos, sqrt, atan2

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points using Haversine formula."""
    R = 6371  # Earth's radius in kilometers
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def calculate_optimal_route(locations: List[Dict]) -> List[Dict]:
    """Find the shortest route visiting all locations using brute force."""
    if len(locations) <= 2:
        return locations
    
    # First location is fixed as starting point
    start = locations[0]
    other_locations = locations[1:]
    
    # Try all possible permutations
    min_distance = float('inf')
    best_route = None
    
    for perm in permutations(other_locations):
        route = [start] + list(perm)
        total_distance = 0
        
        # Calculate total distance for this route
        for i in range(len(route)-1):
            dist = haversine_distance(
                route[i]['lat'], route[i]['lon'],
                route[i+1]['lat'], route[i+1]['lon']
            )
            total_distance += dist
            
        if total_distance < min_distance:
            min_distance = total_distance
            best_route = route
            
    return best_route

def create_route_cards():
    """Create route cards for selected locations."""
    if 'route_cards' not in st.session_state:
        st.session_state.route_cards = []

    active_cards = [card for card in st.session_state.route_cards if card]
    if not active_cards:
        st.info("Select locations on the map to add them to your route.")
        return

    cols = st.columns(4)
    for i, card in enumerate(active_cards):
        with cols[i % 4]:
            st.markdown(f"""
                <div style='padding: 15px; border: 2px solid #4CAF50; border-radius: 8px; margin: 5px; background-color: #f8fff8;'>
                    <h4 style='color: #2E7D32; margin-top: 0;'>{card['name']}</h4>
                    <p style='margin: 8px 0;'>Lat: {card['lat']:.4f}<br>Lon: {card['lon']:.4f}</p>
                    <button style='background: #ff5252; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;' 
                            onclick='removeFromRoute({i})'>Remove</button>
                </div>
            """, unsafe_allow_html=True)

def update_route_card(customer_data: Dict) -> bool:
    """Add customer data to the next available route card."""
    for i in range(8):
        if not st.session_state.route_cards[i]:
            st.session_state.route_cards[i] = customer_data
            return True
    return False

def clear_route_cards():
    """Clear all route cards."""
    st.session_state.route_cards = [None] * 8

def get_active_route() -> List[Dict]:
    """Get list of locations that are currently in route cards."""
    return [card for card in st.session_state.route_cards if card is not None]
