
import pandas as pd

def create_customer_popup(row, format_currency):
    """Create popup content with double-click functionality"""
    popup_content = f"""
    <div style='min-width: 200px'>
        <h4 style="cursor: pointer;" ondblclick='selectCustomer("{row['Name']}", {row['Latitude']}, {row['Longitude']})'>{row['Name']}</h4>
        <b>Address:</b> {row['Corrected_Address']}<br>
        <button onclick='selectCustomer("{row['Name']}", {row['Latitude']}, {row['Longitude']})' 
                style="margin-top: 10px; padding: 5px 10px; background-color: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer;">
            Add to Route
        </button>
        <small style="color: #666; display: block; margin-top: 5px;">Double-click name or click button to add to route</small>
    </div>
    """
    return popup_content
