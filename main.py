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
def load_data():
    try:
        df = pd.read_csv("attached_assets/CustomerGeoLocs.csv")

        # Log the data types of the DataFrame
        st.write("Data Types of columns in CustomerGeoLocs:", df.dtypes)

        # Converting relevant columns to numeric, if necessary
        numeric_columns = ['Latitude', 'Longitude', '3-year Spend', '2024', '2023', '2022']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Log unique values for debugging
        for col in df.columns:
            if df[col].dtype == 'object':
                unique_values = df[col].unique()
                st.write(f"Unique values in {col}:", unique_values)

        return clean_data(df)
    except Exception as e:
        st.error(f"An error occurred while loading the data: {e}")

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

        # Get ProdCodes based on filtered data
        prodcodes = sorted(filtered_df['ProdCode'].unique().tolist())
        selected_prodcode = st.selectbox("Select ProdCode", ["All"] + prodcodes)

        # Further filter based on ProdCode
        if selected_prodcode != "All":
            filtered_df = filtered_df[filtered_df['ProdCode'] == selected_prodcode]

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
                <b>2024:</b> {format_currency(row['2024 '])}<br>
                <b>2023:</b> {format_currency(row['2023 '])}<br>
                <b>2022:</b> {format_currency(row['2022 '])}<br>
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
                    <b>2024:</b> {format_currency(row['2024'])}<br>
                    <b>2023:</b> {format_currency(row['2023'])}<br>
                    <b>2022:</b> {format_currency(row['2022'])}<br>
                    <b>Phone:</b> {row['Phone'] if pd.notna(row['Phone']) else 'N/A'}<br>
                    <b>Address:</b> {row['Corrected_Address']}<br>
                    <small style="color: #666;">(Double-click company name to plan route)</small>
                </div>
                """

                # Calculate marker size based on 3-year spend thresholds
                spend_str = str(row['3-year Spend']).replace('$', '').replace(',', '').strip()
                try:
                    spend = float(re.sub(r'[^\d.-]', '', spend_str)) if spend_str and spend_str != 'nan' else 0
                    # Set radius based on spend categories
                    if isinstance(spend, (int, float)) and spend > 500000:
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
            if pd.notna(row['Latitude']) and pd.notna(row['Longitude']):
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
                    location=[float(row['Latitude']), float(row['Longitude'])],
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

    #
