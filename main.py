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
    .element-container iframe {
        border: 1px solid #ddd;
        min-height: 600px;
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
def load_data(data_source):
    if data_source == "BMC":
        df = pd.read_csv("attached_assets/BMC.csv")
    elif data_source == "BME":
        df = pd.read_csv("attached_assets/BME.csv")
    else:  # MAI
        df = pd.read_csv("attached_assets/MAI.csv")
    return clean_data(df)

# Select data source
data_source = st.radio(
    "Select Data Source",
    ["BMC", "BME", "MAI"],
    horizontal=True
)

# Load and prepare prospects data
@st.cache_data
def load_prospects():
    df_prospects = pd.read_csv("attached_assets/prospectlist.csv")
    df_prospects = df_prospects[df_prospects['latitude'].notna() & df_prospects['longitude'].notna()]
    df_prospects['Revenue Range (in USD)'] = df_prospects['Revenue Range (in USD)'].fillna('Unknown')
    return df_prospects

try:
    df = load_data(data_source)
    prospects_df = load_prospects()

    # Sidebar filters
    with st.sidebar:
        st.header("Filters")

        # Get initial unique values
        states = sorted(df['State/Prov'].unique().tolist())

        # State filter with multi-select (up to 4)
        selected_states = st.multiselect("Select States/Provinces (max 4)", states, max_selections=4)

        # Filter dataframe based on selected states
        filtered_df = df.copy()
        if selected_states:
            filtered_df = filtered_df[filtered_df['State/Prov'].isin(selected_states)]

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
    elif not selected_states and selected_territory == "All" and selected_sales_rep == "All":
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
                    <label class="route-toggle">
                        <input type="checkbox" onclick='selectCustomer("{row['Name']}", {row['Latitude']}, {row['Longitude']})'>
                        <span class="toggle-slider"></span>
                        <span class="toggle-label">Add to Route</span>
                    </label><br><br>
                    <b>Territory:</b> {row['Territory']}<br>
                    <b>Sales Rep:</b> {row['Sales Rep']}<br>
                    <b>3-year Spend:</b> {format_currency(row['3-year Spend'])}<br>
                    <b>2024:</b> {format_currency(row['$2,024 '])}<br>
                    <b>2023:</b> {format_currency(row['$2,023 '])}<br>
                    <b>2022:</b> {format_currency(row['$2,022 '])}<br>
                    <b>Phone:</b> {row['Phone'] if pd.notna(row['Phone']) else 'N/A'}<br>
                    <b>Address:</b> {row['Corrected_Address']}<br>
                    <small style="color: #666;">(Double-click company name to plan route)</small>
                </div>
                """

                # Calculate marker size based on 3-year spend thresholds
                spend_str = str(row['3-year Spend']).replace('$', '').replace(',', '').strip()
                try:
                    spend = float(re.sub(r'[^\d.-]', '', spend_str)) if spend_str else 0
                    # Set radius based on spend categories
                    if spend > 500000:
                        radius = 30  # Largest size
                    elif spend > 100000:
                        radius = 22  # Second largest
                    elif spend > 50000:
                        radius = 15  # Medium size
                    else:
                        radius = 8   # Smallest size
                except:
                    radius = 8  # Default size for parsing errors

                # Check if customer is in selected route
                is_selected = any(c.get('name') == row['Name'] for c in st.session_state.get('selected_customers', []))

                folium.CircleMarker(
                    location=[row['Latitude'], row['Longitude']],
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=row['Name'],
                    radius=radius,
                    color='blue',
                    weight=1.5,
                    fill=True,
                    fill_color='blue' if is_selected else '#3186cc',
                    fill_opacity=0.7 if is_selected else 0.4,
                    opacity=1.0
                ).add_to(m)

        # Add prospect markers
        for index, row in prospects_df.iterrows():
            if pd.notna(row['latitude']) and pd.notna(row['longitude']):
                popup_content = f"""
                    <div style='min-width: 200px'>
                        <h4>Prospect: {row['Company Name']}</h4>
                        <b>Industry:</b> {row['Primary Industry']}<br>
                        <b>Sub-Industry:</b> {row['Primary Sub-Industry']}<br>
                        <b>Address:</b> {row.get('address', 'N/A')}<br>
                        <b>Revenue Range:</b> {row['Revenue Range (in USD)']}<br>
                        <b>Website:</b> <a href='{row['Website']}' target='_blank'>{row['Website']}</a><br>
                        <label class="toggle-switch">
                            <input type="checkbox" onclick='selectCustomer("{row['Company Name']}", {row['latitude']}, {row['longitude']})' 
                                   data-name="{row['Company Name']}">
                            <span class="toggle-slider"></span>
                            <span class="toggle-label">Add to Route</span>
                        </label>
                    </div>
                """
                folium.Marker(
                    location=[float(row['latitude']), float(row['longitude'])],
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=row['Company Name'],
                    icon=folium.Icon(color='green', icon='flag', prefix='fa')
                ).add_to(m)


    # Store the selected customer and widget clicked state
    if 'selected_customer' not in st.session_state:
        st.session_state.selected_customer = None
    if 'widget_clicked' not in st.session_state:
        st.session_state.widget_clicked = None

    # Add JavaScript for customer selection and route planning
    st.markdown("""
        <script>
            var selectedCustomers = new Map();

            function updateRouteCards() {
                const selectedArray = Array.from(selectedCustomers.values());
                window.parent.postMessage({
                    type: 'streamlit:setComponentValue',
                    value: JSON.stringify({
                        type: 'route_selection',
                        customers: selectedArray
                    })
                }, '*');
            }

            // Initialize selected customers from session state
            window.addEventListener('message', function(e) {
                if (e.data.type === 'streamlit:render') {
                    try {
                        if (e.data.componentValue) {
                            const componentValue = JSON.parse(e.data.componentValue);
                            if (Array.isArray(componentValue)) {
                                selectedCustomers.clear();
                                componentValue.forEach(customer => {
                                    selectedCustomers.set(customer.name, customer);
                                });
                                updateAllButtons();
                            }
                        }
                    } catch (err) {
                        console.error('Error parsing component value:', err);
                    }
                }
            });

            function updateAllButtons() {
                document.querySelectorAll('button[data-name]').forEach(button => {
                    const name = button.getAttribute('data-name');
                    updateButtonStyle(button, selectedCustomers.has(name));
                });
            }

            function updateButtonStyle(button, isSelected) {
                const checkbox = button.querySelector('input[type="checkbox"]');
                if (checkbox) {
                    checkbox.checked = isSelected;
                }
            }

            function selectCustomer(name, lat, lon) {
                // Add customer to selected customers for route planning
                const customer = {name: name, lat: lat, lon: lon};

                if (selectedCustomers.has(name)) {
                    selectedCustomers.delete(name);
                } else {
                    if (selectedCustomers.size >= 8) {
                        alert('Maximum 8 locations can be selected for routing');
                        return;
                    }
                    selectedCustomers.set(name, customer);
                }

                // Send updated selection to Streamlit
                const selectedArray = Array.from(selectedCustomers.values());
                if (typeof window.parent.streamlit !== 'undefined') {
                    window.parent.streamlit.setComponentValue({
                        type: 'route_selection',
                        customers: selectedArray
                    });
                }
                setTimeout(() => {
                    window.parent.postMessage({
                        type: 'streamlit:setComponentValue',
                        value: JSON.stringify({
                            type: 'route_selection',
                            customers: selectedArray
                        })
                    }, '*');
                }, 100);
            }
        </script>
    """, unsafe_allow_html=True)

    # Initialize location tracking state
    if 'location_tracking' not in st.session_state:
        st.session_state.location_tracking = False

    # Add location toggle
    location_tracking = st.checkbox('Show My Location', value=st.session_state.location_tracking)

    if location_tracking != st.session_state.location_tracking:
        st.session_state.location_tracking = location_tracking
        if location_tracking:
            st.markdown("""
                <script>
                function updateLocation() {
                    if (navigator.geolocation) {
                        navigator.geolocation.getCurrentPosition(
                            function(position) {
                                window.parent.postMessage({
                                    type: 'streamlit:setComponentValue',
                                    value: JSON.stringify({
                                        type: 'user_location',
                                        lat: position.coords.latitude,
                                        lon: position.coords.longitude
                                    })
                                }, '*');
                                setTimeout(function() {
                                    window.parent.location.reload();
                                }, 100);
                            },
                            function(error) {
                                console.error("Error getting location:", error.message);
                            },
                            {
                                enableHighAccuracy: true,
                                timeout: 5000,
                                maximumAge: 0
                            }
                        );
                    }
                }
                updateLocation();
                </script>
            """, unsafe_allow_html=True)
        else:
            st.session_state.user_location = None
            st.rerun()

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
        .route-toggle {
            position: relative;
            display: inline-flex;
            align-items: center;
            margin: 10px 0;
            cursor: pointer;
            background: #f0f2f6;
            padding: 8px 12px;
            border-radius: 4px;
            transition: all 0.3s ease;
        }
        .route-toggle input {
            opacity: 0;
            width: 0;
            height: 0;
        }
        .route-toggle input:checked + .toggle-slider {
            background-color: #4CAF50;
        }
        .route-toggle input:checked + .toggle-slider:before {
            transform: translateX(26px);
        }
        .route-toggle:hover {
            background: #e3e6f0;
        }
        .toggle-slider {
            position: relative;
            display: inline-block;
            width: 50px;
            height: 24px;
            background-color: #ccc;
            border-radius: 24px;
            transition: .4s;
            margin-right: 10px;
        }
        .toggle-slider:before {
            position: absolute;
            content: "";
            height: 16px;
            width: 16px;
            left: 4px;
            bottom: 4px;
            background-color: white;
            border-radius: 50%;
            transition: .4s;
        }
        .toggle-switch input:checked + .toggle-slider {
            background-color: #4CAF50;
        }
        .toggle-switch input:checked + .toggle-slider:before {
            transform: translateX(26px);
        }
        .toggle-label {
            font-weight: bold;
            color: #333;
        }
        </style>
    """, unsafe_allow_html=True)

    # Initialize session state variables
    if 'selected_customers' not in st.session_state:
        st.session_state.selected_customers = []
    if 'user_location' not in st.session_state:
        st.session_state.user_location = None

    # Handle component value updates
    if st.session_state.get('_component_value'):
        try:
            selected = st.session_state._component_value
            if isinstance(selected, str):
                selected = eval(selected)
            if isinstance(selected, dict):
                if selected.get('type') == 'route_selection':
                    customers = selected.get('customers', [])
                    st.session_state.selected_customers = customers
                    if customers:
                        # Select the first customer in the route for details display
                        st.session_state.selected_customer = customers[0]['name']
                    st.rerun()
        except Exception as e:
            st.error(f"Error handling selection: {str(e)}")

    # Add user location marker if available
    if st.session_state.user_location:
        folium.Marker(
            location=[st.session_state.user_location['lat'], st.session_state.user_location['lon']],
            popup='Your Location',
            icon=folium.Icon(color='green', icon='user', prefix='fa'),
            tooltip='Your Location'
        ).add_to(m)

    from route_planner import create_route_cards, calculate_optimal_route, clear_route_cards, get_active_route

    # Display route planning cards
    st.markdown("### Route Planning")
    create_route_cards()

    # Add Plan Trip button
    if st.button("Plan Trip"):
        route = get_active_route()
        if len(route) >= 2:
            optimal_route = calculate_optimal_route(route)

            # Draw optimal route on map
            coordinates = [(loc['lat'], loc['lon']) for loc in optimal_route]
            folium.PolyLine(
                coordinates,
                weight=2,
                color='red',
                opacity=0.8
            ).add_to(m)

            # Display route summary
            total_distance = 0
            st.markdown("### Route Summary")
            for i in range(len(optimal_route)):
                st.write(f"{i+1}. {optimal_route[i]['name']}")
                if i < len(optimal_route) - 1:
                    dist = haversine_distance(
                        optimal_route[i]['lat'], optimal_route[i]['lon'],
                        optimal_route[i+1]['lat'], optimal_route[i+1]['lon']
                    )
                    total_distance += dist
            st.write(f"\nTotal distance: {total_distance:.1f} km")
        else:
            st.warning("Please select at least 2 locations for route planning")

    # Clear route button
    if st.button("Clear Route"):
        clear_route_cards()
        st.rerun()

    # Display the map
    folium_static(m, width=1200, height=600)

    if st.session_state.selected_customer:
        selected_data = filtered_df[filtered_df['Name'] == st.session_state.selected_customer]
        if not selected_data.empty:
            lat = selected_data['Latitude'].iloc[0]
            lon = selected_data['Longitude'].iloc[0]

            # Add selected customer marker
            folium.Marker(
                location=[lat, lon],
                popup=selected_data['Name'].iloc[0],
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)

    # Handle customer selection
    if st.session_state.widget_clicked:
        st.session_state.selected_customer = st.session_state.widget_clicked
        st.rerun()

    # Display selected customer details in a placeholder card
    st.markdown("### Customer Details")
    details_placeholder = st.empty()

    if st.session_state.selected_customers:
        selected_names = [c['name'] for c in st.session_state.selected_customers]
        selected_customer = st.selectbox("Select customer to view details:", selected_names)

        if selected_customer:
            customer_data = filtered_df[filtered_df['Name'] == selected_customer]
            if not customer_data.empty:
                row = customer_data.iloc[0]
                with details_placeholder.container():
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.markdown(f"### {row['Name']}")
                        st.write(f"**Territory:** {row['Territory']}")
                        st.write(f"**Sales Rep:** {row['Sales Rep']}")
                        st.write(f"**3-year Spend:** {format_currency(row['3-year Spend'])}")
                        st.write(f"**Phone:** {row['Phone'] if pd.notna(row['Phone']) else 'N/A'}")
                        st.write(f"**Address:** {row['Corrected_Address']}")
                    with col2:
                        if st.button("Remove from Route", key=f"remove_{selected_customer}"):
                            st.session_state.selected_customers = [
                                c for c in st.session_state.selected_customers 
                                if c['name'] != selected_customer
                            ]
                            st.rerun()
    else:
        details_placeholder.info("Select customers on the map to view their details here.")

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