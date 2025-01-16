
def create_customer_popup(row, format_currency):
    """Create popup content with double-click functionality"""
    popup_content = f"""
    <div style='min-width: 200px'>
        <h4 style="cursor: pointer;" ondblclick='selectCustomer("{row['Name']}", {row['Latitude']}, {row['Longitude']})'>{row['Name']}</h4>
        <b>Territory:</b> {row['Territory']}<br>
        <b>Sales Rep:</b> {row['Sales Rep']}<br>
        <b>3-year Spend:</b> {format_currency(row['3-year Spend'])}<br>
        <b>2024:</b> {format_currency(row['$2,024 '])}<br>
        <b>2023:</b> {format_currency(row['$2,023 '])}<br>
        <b>2022:</b> {format_currency(row['$2,022 '])}<br>
        <b>Phone:</b> {row['Phone'] if pd.notna(row['Phone']) else 'N/A'}<br>
        <b>Address:</b> {row['Corrected_Address']}<br>
        <small style="color: #666;">(Double-click company name to plan route)</small>
    </div>
    """
    return popup_content
