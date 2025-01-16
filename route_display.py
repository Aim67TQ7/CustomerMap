
import streamlit as st
import folium
from streamlit_folium import st_folium
from utils import format_currency

def display_route(route, distances, filtered_df):
    st.set_page_config(layout="wide", page_title="Route Details")
    st.title("Optimal Route Details")
    
    # Create map with route
    center_lat = sum(float(c['lat']) for c in route) / len(route)
    center_lon = sum(float(c['lon']) for c in route) / len(route)
    m = folium.Map(location=[center_lat, center_lon], zoom_start=6)
    
    # Draw route line
    coordinates = [(c['lat'], c['lon']) for c in route]
    folium.PolyLine(coordinates, weight=2, color='red', opacity=0.8).add_to(m)
    
    # Add markers
    for i, customer in enumerate(route):
        folium.Marker(
            location=[customer['lat'], customer['lon']],
            popup=f"Stop {i+1}: {customer['name']}",
            icon=folium.Icon(color='red' if i == 0 else 'blue', icon='info-sign')
        ).add_to(m)
    
    # Display map
    st_folium(m, width=1200)
    
    # Print-friendly route details
    st.markdown("### Route Summary")
    total_distance = sum(d['distance'] for d in distances)
    st.write(f"Total Distance: {total_distance:.1f} km")
    
    # Customer table
    st.markdown("### Stops")
    stops_data = []
    for i, customer in enumerate(route):
        customer_info = filtered_df[filtered_df['Name'] == customer['name']].iloc[0]
        stops_data.append({
            "Stop": i + 1,
            "Customer": customer['name'],
            "Address": customer_info['Corrected_Address']
        })
    
    st.table(stops_data)
    
    # Print button
    st.markdown("""
        <style>
        @media print {
            .stApp { padding: 0; }
            iframe { height: 300px !important; }
        }
        </style>
        <script>
        function printRoute() {
            window.print();
        }
        </script>
    """, unsafe_allow_html=True)
    
    if st.button("Print Route"):
        st.markdown("<script>printRoute()</script>", unsafe_allow_html=True)
