import pandas as pd
import re

def clean_data(df):
    """Clean and prepare the customer data."""
    # Standardize column names
    column_mapping = {
        'lat': 'Latitude',
        'latitude': 'Latitude',
        'lon': 'Longitude',
        'longitude': 'Longitude',
        'phone': 'Phone',
        'territory': 'Territory',
        'sales_rep': 'Sales Rep',
        'prodcode': 'ProdCode',
        'state': 'State/Prov',
        'state/prov': 'State/Prov',
        'stateprov': 'State/Prov',
        'state/province': 'State/Prov',
        'name': 'Name',
        'company name': 'Name',
        'customer name': 'Name',
        '3-year spend': '3-year Spend',
        '3 year spend': '3-year Spend',
        'three year spend': '3-year Spend'
    }
    
    # Rename columns if they exist (case-insensitive)
    for col in df.columns:
        lower_col = col.lower()
        for old_col, new_col in column_mapping.items():
            if lower_col == old_col:
                df = df.rename(columns={col: new_col})
    
    # Remove rows with invalid coordinates
    df = df[df['Latitude'].notna() & df['Longitude'].notna()]
    
    # Convert coordinates to float
    df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
    df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
    
    # Remove any rows where conversion to float failed
    df = df.dropna(subset=['Latitude', 'Longitude'])
    
    # Clean phone numbers if Phone column exists
    if 'Phone' in df.columns:
        df['Phone'] = df['Phone'].astype(str).apply(clean_phone_number)
    
    # Ensure required columns exist
    required_columns = ['Territory', 'Sales Rep', 'State/Prov', 'ProdCode']
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

def format_currency(value):
    """Format currency values consistently."""
    if pd.isna(value) or value == ' $-   ' or value == '0':
        return '$0'
        
    # Remove any existing formatting
    value_str = str(value)
    value_str = re.sub(r'[^\d.-]', '', value_str)
    
    try:
        # Convert to float and format
        amount = float(value_str)
        return f"${amount:,.2f}"
    except ValueError:
        return '$0'
