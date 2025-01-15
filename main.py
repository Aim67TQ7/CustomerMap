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

    # Create base map centered on filtered data
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

    # Store the selected customer in session state
    if 'selected_customer' not in st.session_state:
        st.session_state.selected_customer = None

    # Custom CSS for layout
    st.markdown("""
        <style>
        .map-container {
            position: relative;
            width: 75%;
            float: left;
            padding-right: 0;
        }
        .list-container {
            position: relative;
            width: 25%;
            float: right;
            height: 600px;
            overflow-y: auto;
            background: white;
            padding: 10px;
            border-left: 1px solid #ddd;
        }
        .customer-link {
            display: block;
            padding: 8px;
            text-decoration: none;
            color: #1f77b4;
            border-bottom: 1px solid #eee;
        }
        .customer-link:hover {
            background: #f5f5f5;
        }
        .customer-link.selected {
            background: #e6f3ff;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

    # Create container divs
    st.markdown('<div class="map-container">', unsafe_allow_html=True)
    # Update map based on selection
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

        folium_static(m)
    st.markdown('</div>', unsafe_allow_html=True)

    # Customer list container
    st.markdown('<div class="list-container">', unsafe_allow_html=True)
    st.markdown("### Customer List")
    customer_list = filtered_df['Name'].sort_values().tolist()

    # Create customer links
    for customer in customer_list:
        is_selected = customer == st.session_state.selected_customer
        selected_class = " selected" if is_selected else ""
        
        if st.markdown(f'<a href="#" class="customer-link{selected_class}" onclick="streamlit_click(\'{customer}\')">{customer}</a>', unsafe_allow_html=True):
            if st.session_state.selected_customer == customer:
                st.session_state.selected_customer = None
            else:
                st.session_state.selected_customer = customer
                selected_data = filtered_df[filtered_df['Name'] == customer].iloc[0]
                st.markdown(f"""
                    **Territory:** {selected_data['Territory']}<br>
                    **Sales Rep:** {selected_data['Sales Rep']}<br>
                    **3-year Spend:** {format_currency(selected_data['3-year Spend'])}
                """, unsafe_allow_html=True)
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

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