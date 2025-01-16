
import pandas as pd

def create_customer_popup(row, format_currency):
    """Create popup content with double-click functionality"""
    popup_content = f"""
    <div style='min-width: 200px'>
        <h4 style="cursor: pointer;" ondblclick='selectCustomer("{row['Name']}", {row['Latitude']}, {row['Longitude']})'>{row['Name']}</h4>
        <b>Address:</b> {row['Corrected_Address']}<br>
        <small style="color: #666;">(Double-click name to add to route)</small>
    </div>
    """
    return popup_content
