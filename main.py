import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from utils import clean_data, format_currency

# Page configuration
st.set_page_config(
    page_title="Customer Location Viewer",
    page_icon="🌎",
    layout="wide" 
)

# Add custom CSS
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stButton>button {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# Title
st.title("Bunting-Newton")
st.markdown("### Customer Location Viewer")

from database import init_db, register_user, verify_user

# Initialize database
init_db()

# Session state initialization
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None

# Authentication UI
if not st.session_state.authenticated:
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        username = st.text_input("Username:", key="login_username")
        password = st.text_input("Password:", type="password", key="login_password")
        if st.button("Login"):
            user = verify_user(username, password)
            if user:
                st.session_state.authenticated = True
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        reg_username = st.text_input("Username:", key="reg_username")
        reg_password = st.text_input("Password:", type="password", key="reg_password")
        reg_password2 = st.text_input("Confirm Password:", type="password")
        if st.button("Register"):
            if reg_password != reg_password2:
                st.error("Passwords don't match")
            elif not reg_username.endswith('@buntingmagnetics.com'):
                st.error("Username must be a valid @buntingmagnetics.com email address")
            elif register_user(reg_username, reg_password):
                st.success("Registration successful! Please login.")
            else:
                st.error("Username already exists or is invalid")

    st.stop()  # Stop execution here if not authenticated

# Load and clean data
@st.cache_data
def load_data():
    df = pd.read_csv("attached_assets/CustomerGeoLocs.csv")
    return clean_data(df)

# Load and prepare prospects data
@st.cache_data
def load_prospects():
    df_prospects = pd.read_csv("attached_assets/prospectlist.csv")
    df_prospects = df_prospects[df_prospects['latitude'].notna() & df_prospects['longitude'].notna()]
    df_prospects['Revenue Range (in USD)'] = df_prospects['Revenue Range (in USD)'].fillna('Unknown')
    return df_prospects

try:
    df = load_data()
    prospects_df = load_prospects()

    # Sidebar filters
    with st.sidebar:
        st.header("Filters")

        # Get initial unique values
        states = sorted(df['State/Prov'].unique().tolist())

        # State filter
        selected_state = st.selectbox("Select State/Province", ["All"] + states)

        # Filter dataframe based on state
        filtered_df = df.copy()
        if selected_state != "All":
            filtered_df = filtered_df[filtered_df['State/Prov'] == selected_state]

        # Get territories based on filtered data
        territories = sorted(filtered_df['Territory'].unique().tolist())
        selected_territory = st.selectbox("Select Territory", ["All"] + territories)

        # Further filter based on territory
        if selected_territory != "All":
            filtered_df = filtered_df[filtered_df['Territory'] == selected_territory]

        # Get sales reps based on filtered data
        sales_reps = sorted(filtered_df['Sales Rep'].unique().tolist())
        selected_sales_rep = st.selectbox("Select Sales Rep", ["All"] + sales_reps)

        # Further filter based on sales rep
        if selected_sales_rep != "All":
            filtered_df = filtered_df[filtered_df['Sales Rep'] == selected_sales_rep]

        # Get customer names based on all applied filters
        customer_names = sorted(filtered_df['Name'].unique().tolist())
        st.subheader("Customer Search")
        search_term = st.selectbox("Select customer:", ["All"] + customer_names)

    # Initial locations
    initial_locations = [
        {"name": "Bunting-Newton", "lat": 37.3043, "lon": -97.4395, "address": "500 S Spencer St, Newton, KS 67114"},
        {"name": "Bunting Elk Grove", "lat": 42.0361, "lon": -87.9303, "address": "1150 Howard St, Elk Grove Village, IL 60007"},
        {"name": "Bunting-Magnet Applications", "lat": 41.1201, "lon": -78.8391, "address": "12 Industrial Dr, DuBois, PA 15801"}
    ]

    # Create base map
    if search_term != "All":
        # Show only selected customer
        customer_data = filtered_df[filtered_df['Name'] == search_term]
        if not customer_data.empty:
            center_lat = customer_data['Latitude'].iloc[0]
            center_lon = customer_data['Longitude'].iloc[0]
            m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

            # Add marker for selected customer
            row = customer_data.iloc[0]
            popup_content = f"""
            <div style='min-width: 200px'>
                <h4>{row['Name']}</h4>
                <b>Territory:</b> {row['Territory']}<br>
                <b>Sales Rep:</b> {row['Sales Rep']}<br>
                <b>3-year Spend:</b> {format_currency(row['3-year Spend'])}<br>
                <b>2024:</b> {format_currency(row['$2,024 '])}<br>
                <b>2023:</b> {format_currency(row['$2,023 '])}<br>
                <b>2022:</b> {format_currency(row['$2,022 '])}<br>
                <b>Phone:</b> {row['Phone'] if pd.notna(row['Phone']) else 'N/A'}<br>
                <b>Address:</b> {row['Corrected_Address']}<br>
            </div>
            """
            folium.Marker(
                location=[row['Latitude'], row['Longitude']],
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=row['Name'],
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(m)
    elif selected_state == "All" and selected_territory == "All" and selected_sales_rep == "All":
        # Show only initial locations if no filters are applied
        center_lat = sum(loc["lat"] for loc in initial_locations) / len(initial_locations)
        center_lon = sum(loc["lon"] for loc in initial_locations) / len(initial_locations)
        m = folium.Map(location=[center_lat, center_lon], zoom_start=4)

        # Add markers for initial locations
        for loc in initial_locations:
            popup_content = f"""
            <div style='min-width: 200px'>
                <h4>{loc['name']}</h4>
                <b>Address:</b> {loc['address']}<br>
            </div>
            """
            folium.Marker(
                location=[loc['lat'], loc['lon']],
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=loc['name'],
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)
    else:
        # Use filtered data when filters are applied
        center_lat = filtered_df['Latitude'].mean()
        center_lon = filtered_df['Longitude'].mean()
        m = folium.Map(location=[center_lat, center_lon], zoom_start=4)

        # Add markers for each customer
        for idx, row in filtered_df.iterrows():
            if pd.notna(row['Latitude']) and pd.notna(row['Longitude']):
                # Create popup content with selection button
                popup_content = f"""
                <div style='min-width: 200px'>
                    <h4>{row['Name']}</h4>
                    <b>Territory:</b> {row['Territory']}<br>
                    <b>Sales Rep:</b> {row['Sales Rep']}<br>
                    <b>3-year Spend:</b> {format_currency(row['3-year Spend'])}<br>
                    <b>2024:</b> {format_currency(row['$2,024 '])}<br>
                    <b>2023:</b> {format_currency(row['$2,023 '])}<br>
                    <b>2022:</b> {format_currency(row['$2,022 '])}<br>
                    <b>Phone:</b> {row['Phone'] if pd.notna(row['Phone']) else 'N/A'}<br>
                    <b>Address:</b> {row['Corrected_Address']}<br>
                    <button onclick='selectCustomer("{row['Name']}", {row['Latitude']}, {row['Longitude']})' 
                    style='margin-top: 10px; padding: 8px 16px; background-color: #4CAF50; color: white; 
                    border: none; border-radius: 4px; cursor: pointer; font-weight: bold;'>
                    📍 Select for Route</button>
                </div>
                """

                folium.Marker(
                    location=[row['Latitude'], row['Longitude']],
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=row['Name'],
                    icon=folium.Icon(color='blue', icon='info-sign')
                ).add_to(m)

        # Add prospect markers
        for index, row in prospects_df.iterrows():
            popup_content = f"""
                <div style='min-width: 200px'>
                    <h4>Prospect: {row['Company Name']}</h4>
                    <b>Address:</b> {row['address']}<br>
                    <b>Revenue Range:</b> {row['Revenue Range (in USD)']}<br>
                    <b>Website:</b> <a href='{row['Website']}' target='_blank'>{row['Website']}</a><br>
                </div>
            """
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=row['Company Name'],
                icon=folium.Icon(color='green', icon='info-sign')
            ).add_to(m)


    # Store the selected customer and widget clicked state
    if 'selected_customer' not in st.session_state:
        st.session_state.selected_customer = None
    if 'widget_clicked' not in st.session_state:
        st.session_state.widget_clicked = None

    # Add JavaScript for customer selection and route planning
    st.markdown("""
        <script>
            var selectedCustomers = [];

            function selectCustomer(name, lat, lon) {
                if (selectedCustomers.length >= 10) {
                    alert('Maximum 10 customers can be selected for routing');
                    return;
                }

                selectedCustomers.push({name: name, lat: lat, lon: lon});
                updateRoute();
            }

            function updateRoute() {
                if (selectedCustomers.length >= 2) {
                    // Send selected customers to Streamlit
                    window.parent.postMessage({
                        type: 'streamlit:setComponentValue',
                        value: JSON.stringify(selectedCustomers)
                    }, '*');
                }
            }
        </script>
    """, unsafe_allow_html=True)

    # Add user location finder
    st.markdown("""
        <script>
        function findUserLocation() {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    function(position) {
                        // Send location to Streamlit
                        window.parent.postMessage({
                            type: 'streamlit:setComponentValue',
                            value: JSON.stringify({
                                type: 'user_location',
                                lat: position.coords.latitude,
                                lon: position.coords.longitude
                            })
                        }, '*');
                        // Reload the page to update the map
                        window.parent.location.reload();
                    },
                    function(error) {
                        alert("Error getting location: " + error.message);
                    },
                    {
                        enableHighAccuracy: true,
                        timeout: 5000,
                        maximumAge: 0
                    }
                );
            } else {
                alert("Geolocation is not supported by this browser.");
            }
        }
        </script>
        <button onclick="findUserLocation()" style="margin: 10px 0; padding: 8px 12px; background-color: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer;">
            <i class="fas fa-star"></i> Find My Location
        </button>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    """, unsafe_allow_html=True)

    # Custom CSS for layout
    st.markdown("""
        <style>
        .stApp {
            margin: 0;
            padding: 0;
        }
        .main {
            display: flex;
            flex-direction: row;
            gap: 1rem;
        }
        .customer-list {
            height: 600px;
            overflow-y: auto;
            border: 1px solid #eee;
            margin-top: 0;
            font-size: 0.5em;
            background: white;
        }
        .customer-link {
            display: block;
            padding: 4px 8px;
            margin: 1px 0;
            text-decoration: none;
            color: #1e88e5;
            cursor: pointer;
            font-size: 14px;
        }
        .customer-link:hover {
            background-color: #f0f2f6;
        }
        .customer-link.selected {
            background-color: #e3f2fd;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

    # Initialize session state variables
    if 'selected_customers' not in st.session_state:
        st.session_state.selected_customers = []
    if 'user_location' not in st.session_state:
        st.session_state.user_location = None

    # Add user location marker if available
    if st.session_state.user_location:
        folium.Marker(
            location=[st.session_state.user_location['lat'], st.session_state.user_location['lon']],
            popup='Your Location',
            icon=folium.Icon(color='green', icon='user', prefix='fa'),
            tooltip='Your Location'
        ).add_to(m)

    # Add route calculation function
    def calculate_optimal_route(points):
        if len(points) < 2:
            return points

        # Start with first point
        unvisited = points[1:]
        current = points[0]
        route = [current]

        # Find nearest neighbor repeatedly
        while unvisited:
            nearest = min(unvisited, key=lambda x: ((x['lat'] - current['lat'])**2 + 
                                                   (x['lon'] - current['lon'])**2)**0.5)
            route.append(nearest)
            current = nearest
            unvisited.remove(nearest)

        return route

    # Map container
    selected_customers = st.session_state.get('selected_customers', [])

    # Add custom CSS for the floating button
    st.markdown("""
        <style>
        .floating-button-container {
            position: absolute;
            bottom: 20px;
            left: 20px;
            z-index: 1000;
        }
        .calculate-route-button {
            background-color: #1E88E5;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        .clear-route-button {
            background-color: #dc3545;
            margin-right: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Create container for floating buttons
    st.markdown("""
        <div class='floating-button-container'>
            <button class='calculate-route-button clear-route-button' onclick='clearRoute()'>Clear Route</button>
            <button class='calculate-route-button' onclick='calculateRoute()'>Calculate Optimal Route</button>
        </div>
    """, unsafe_allow_html=True)

    if st.button('Clear Route', key='hidden_clear'):
        st.session_state.selected_customers = []
        st.rerun()

    if st.button('Calculate Optimal Route', key='hidden_calculate'):
        if len(st.session_state.selected_customers) < 2:
            st.warning('Please select at least 2 customers to calculate a route.')
        else:
            st.session_state.selected_customers = calculate_optimal_route(st.session_state.selected_customers)
            st.rerun()

    # Add JavaScript for button functionality
    st.markdown("""
        <script>
        function clearRoute() {
            document.querySelector('[data-testid="stButton"] button[key="hidden_clear"]').click();
        }
        function calculateRoute() {
            document.querySelector('[data-testid="stButton"] button[key="hidden_calculate"]').click();
        }
        </script>
    """, unsafe_allow_html=True)

    # Map container
    selected_customers = st.session_state.get('selected_customers', [])

    # Draw routes if customers are selected
    if len(selected_customers) >= 2:
        # Create route coordinates
        coordinates = [(c['lat'], c['lon']) for c in selected_customers]

        # Draw route line
        folium.PolyLine(
            coordinates,
            weight=2,
            color='red',
            opacity=0.8
        ).add_to(m)

    if st.session_state.selected_customer:
        selected_data = filtered_df[filtered_df['Name'] == st.session_state.selected_customer]
        if not selected_data.empty:
            lat = selected_data['Latitude'].iloc[0]
            lon = selected_data['Longitude'].iloc[0]
            m = folium.Map(location=[lat, lon], zoom_start=12)

            # Add selected customer marker
            folium.Marker(
                location=[lat, lon],
                popup=selected_data['Name'].iloc[0],
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)
    folium_static(m, width=1200)

    # Handle customer selection
    if st.session_state.widget_clicked:
        st.session_state.selected_customer = st.session_state.widget_clicked
        st.rerun()

    if search_term and search_term != "All":
        search_results = filtered_df[filtered_df['Name'] == search_term]

        for _, row in search_results.iterrows():
            with st.expander(row['Name']):
                st.write(f"**Territory:** {row['Territory']}")
                st.write(f"**Sales Rep:** {row['Sales Rep']}")
                st.write(f"**3-year Spend:** {format_currency(row['3-year Spend'])}")
                st.write(f"**Phone:** {row['Phone'] if pd.notna(row['Phone']) else 'N/A'}")
                st.write(f"**Address:** {row['Corrected_Address']}")

except Exception as e:
    st.error(f"An error occurred while loading the data: {str(e)}")
    st.write("Please check if the data file is in the correct location and format.")