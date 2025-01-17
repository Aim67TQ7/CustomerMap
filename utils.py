import pandas as pd
import re

def clean_data(df):
    """Clean and prepare the customer data."""
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
