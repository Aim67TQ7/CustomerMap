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

@st.cache_data
def load_mai_data():
    df_mai = pd.read_csv("attached_assets/MAI_CustomerGeoLocs.csv")
    return clean_data(df_mai)

try:
    df = load_data()
    prospects_df = load_prospects()
    mai_df = load_mai_data()

    # Add data source selector
    data_source = st.radio("Select Data Source", ["BMC Customers", "MAI Customers"], horizontal=True)
    
    # Select the appropriate dataset based on user choice
    filtered_df = mai_df if data_source == "MAI Customers" else df

    # Sidebar filters
    with st.sidebar:
        st.header("Filters")

        # Remove nearby prospects search from sidebar
        from math import radians, sin, cos, sqrt, atan2

        def calculate_distance(lat1, lon1, lat2, lon2):
            R = 3959  # Earth's radius in miles
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            return R * c

        states = sorted(df['State/Prov'].unique().tolist())

        selected_states = st.multiselect("Select States/Provinces (max 4)", states, max_selections=4)

        filtered_df = df.copy()
        if selected_states:
            filtered_df = filtered_df[filtered_df['State/Prov'].isin(selected_states)]

        territories = sorted(filtered_df['Territory'].unique().tolist())
        selected_territory = st.selectbox("Select Territory", ["All"] + territories)

        if selected_territory != "All":
            filtered_df = filtered_df[filtered_df['Territory'] == selected_territory]

        sales_reps = sorted(filtered_df['Sales Rep'].unique().tolist())
        selected_sales_rep = st.selectbox("Select Sales Rep", ["All"] + sales_reps)

        if selected_sales_rep != "All":
            filtered_df = filtered_df[filtered_df['Sales Rep'] == selected_sales_rep]

        customer_names = sorted(filtered_df['Name'].unique().tolist())
        st.subheader("Customer Search")
        search_term = st.selectbox("Select customer:", ["All"] + customer_names)

    initial_locations = [
        {"name": "Bunting-Newton", "lat": 37.3043, "lon": -97.4395, "address": "500 S Spencer St, Newton, KS 67114"},
        {"name": "Bunting Elk Grove", "lat": 42.0361, "lon": -87.9303, "address": "1150 Howard St, Elk Grove Village, IL 60007"},
        {"name": "Bunting-Magnet Applications", "lat": 41.1201, "lon": -78.8391, "address": "12 Industrial Dr, DuBois, PA 15801"}
    ]

    if search_term != "All":
        customer_data = filtered_df[filtered_df['Name'] == search_term]
        if not customer_data.empty:
            center_lat = customer_data['Latitude'].iloc[0]
            center_lon = customer_data['Longitude'].iloc[0]
            m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

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
    else:
        center_lat = sum(loc["lat"] for loc in initial_locations) / len(initial_locations)
        center_lon = sum(loc["lon"] for loc in initial_locations) / len(initial_locations)
        m = folium.Map(location=[center_lat, center_lon], zoom_start=4)

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

    folium_static(m, width=1200)

except Exception as e:
    st.error(f"An error occurred while loading the data: {str(e)}")
    st.write("Please check if the data file is in the correct location and format.")
