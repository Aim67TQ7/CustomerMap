
import pandas as pd
import re

def clean_data(df):
    """Clean and prepare the customer data."""
    # Standardize column names
    column_mapping = {
        '3-year Spend': '3-year Spend',
        'Name': 'Name',
        'Name.1': 'Name',
        'Territory': 'Territory',
        'Sales Rep': 'Sales Rep',
        'Phone': 'Phone',
        'Latitude': 'Latitude',
        'Longitude': 'Longitude',
        'Corrected_Address': 'Corrected_Address'
    }
    
    # Rename columns if they exist
    for old_col, new_col in column_mapping.items():
        if old_col in df.columns and old_col != new_col:
            df = df.rename(columns={old_col: new_col})
    
    # Remove rows with invalid coordinates
    df = df[df['Latitude'].notna() & df['Longitude'].notna()]
    
    # Remove rows with "Error" in coordinates
    df = df[~(df['Latitude'].astype(str).str.contains('Error', na=False)) & 
            ~(df['Longitude'].astype(str).str.contains('Error', na=False))]
    
    # Convert coordinates to float
    df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
    df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
    
    # Remove any rows where conversion to float failed
    df = df.dropna(subset=['Latitude', 'Longitude'])
    
    # Clean phone numbers
    df['Phone'] = df['Phone'].astype(str).apply(clean_phone_number)
    
    # Ensure required columns exist
    required_columns = ['Name', 'Territory', 'Sales Rep', '3-year Spend', 'Phone', 'Latitude', 'Longitude', 'Corrected_Address']
    for col in required_columns:
        if col not in df.columns:
            df[col] = ''
    
    return df

def clean_phone_number(phone):
    """Clean and format phone numbers."""
    if pd.isna(phone) or phone == '0' or phone == 'nan':
        return ''
    
    # Remove non-numeric characters
    nums = re.sub(r'\D', '', str(phone))
    
    # Format number if it has enough digits
    if len(nums) >= 10:
        return f"({nums[-10:-7]}) {nums[-7:-4]}-{nums[-4:]}"
    return phone
