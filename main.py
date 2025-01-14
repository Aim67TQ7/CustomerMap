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

# Access code verification
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# Create the access code input field
if not st.session_state.authenticated:
    access_code = st.text_input("Enter access code:", type="password")
    if st.button("Submit"):
        if access_code == "1Bunting!":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect access code. Please try again.")
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

    # Display the map and search
    col1, col2 = st.columns([2, 1])

    with col1:
        folium_static(m, width=800)

    with col2:
        st.markdown("### Customer Search")
        search_term = st.text_input("Search by customer name:")

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
