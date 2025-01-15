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

try:
    df = load_data()

    # Sidebar filters
    with st.sidebar:
        st.header("Filters")

        # Customer Search
        st.subheader("Customer Search")
        search_term = st.text_input("Search by customer name:")

        # Get unique values for filters
        states = sorted(df['State/Prov'].unique().tolist())
        territories = sorted(df['Territory'].unique().tolist())
        sales_reps = sorted(df['Sales Rep'].unique().tolist())

        # Add "All" option to each filter
        selected_state = st.selectbox("Select State/Province", ["All"] + states)
        selected_territory = st.selectbox("Select Territory", ["All"] + territories)
        selected_sales_rep = st.selectbox("Select Sales Rep", ["All"] + sales_reps)

        # Apply filters to dataframe
        filtered_df = df.copy()
        if selected_state != "All":
            filtered_df = filtered_df[filtered_df['State/Prov'] == selected_state]
        if selected_territory != "All":
            filtered_df = filtered_df[filtered_df['Territory'] == selected_territory]
        if selected_sales_rep != "All":
            filtered_df = filtered_df[filtered_df['Sales Rep'] == selected_sales_rep]

    # Initial locations
    initial_locations = [
        {"name": "Bunting-Newton", "lat": 37.3043, "lon": -97.4395, "address": "500 S Spencer St, Newton, KS 67114"},
        {"name": "Bunting Elk Grove", "lat": 42.0361, "lon": -87.9303, "address": "1150 Howard St, Elk Grove Village, IL 60007"},
        {"name": "Bunting-Magnet Applications", "lat": 41.1201, "lon": -78.8391, "address": "12 Industrial Dr, DuBois, PA 15801"}
    ]

    # Create base map
    if not (selected_state != "All" or selected_territory != "All" or selected_sales_rep != "All" or search_term):
        # Show only initial locations if no filters
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
                # Create popup content
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

    # Store the selected customer and widget clicked state
    if 'selected_customer' not in st.session_state:
        st.session_state.selected_customer = None
    if 'widget_clicked' not in st.session_state:
        st.session_state.widget_clicked = None

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

    # Map container
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

    if search_term:
        search_results = filtered_df[filtered_df['Name'].str.contains(search_term, case=False, na=False)]

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