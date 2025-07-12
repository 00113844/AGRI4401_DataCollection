import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from PIL import Image
from urllib.parse import quote

# Page configuration
st.set_page_config(
    page_title="Geostatistics Field Data",
    page_icon="🗺️",
    layout="wide"
)

# Sample data - replace with your actual data
def load_data():
    """Load sampling point data from CSV file"""
    try:
        # read CSV with columns: UID, MAP, POINT, Clay_percent, P_ppm, K_ppm, NDVI, pH
        return pd.read_csv("data/points.csv")
    except FileNotFoundError:
        st.error("Data file not found: data/points.csv. Please add your 43-point CSV.")
        return pd.DataFrame()

def generate_qr_code(url):
    """Generate QR code for a given URL, enforcing https://"""
    if not url.lower().startswith(("http://", "https://")):
        url = "https://" + url               # <-- ensure scheme
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    return img

def main():
    st.title("🗺️ Geostatistics Field Data Collection")
    df = load_data()

    # old: uid_list = st.query_params.get("uid", [])
    # new: always use get_all() so it's a list
    params   = st.query_params
    uid_list = params.get_all("uid")
    if uid_list:
        uid = uid_list[0]  # full UID, not just the first char
        point_data = df[df["UID"].astype(str) == uid]
        if not point_data.empty:
            show_point_detail(point_data.iloc[0])
        else:
            st.error(f"Record {uid} not found")
    else:
        # Protected admin interface
        ADMIN_PASSWORD = "changeme"
        if not st.session_state.get("authenticated", False):
            st.subheader("Admin Login")
            pwd = st.text_input("Enter admin password", type="password")
            if st.button("Login"):
                if pwd == ADMIN_PASSWORD:
                    st.session_state.authenticated = True
                    st.success("Logged in successfully")
                else:
                    st.error("Incorrect password")
        if st.session_state.get("authenticated", False):
            show_admin_interface(df)

def show_point_detail(point):
    """Display all five parameters for one UID."""
    # Header
    st.header(f"UID: {point['UID']}  |  Map: {point['MAP']}  |  Point: {point['POINT']}")
    
    # Display each metric
    st.metric("Clay %",   f"{point['Clay_percent']}%")
    st.metric("P (ppm)",  point["P_ppm"])
    st.metric("K (ppm)",  point["K_ppm"])
    st.metric("NDVI",     f"{point['NDVI']:.2f}")
    st.metric("pH",       f"{point['pH']:.1f}")
    
    # Instructions
    st.info("""
    **Instructions:**
    1. Record the RTK coordinates at this location
    2. Note the parameter values above
    3. Proceed to the next point
    """)
    
    # Optional: Add a form for students to input their RTK measurements
    with st.expander("Record Your RTK Measurements"):
        col1, col2 = st.columns(2)
        with col1:
            rtk_lat = st.number_input("RTK Latitude", format="%.6f")
            student_name = st.text_input("Student Name")
        with col2:
            rtk_lon = st.number_input("RTK Longitude", format="%.6f")
            group_name = st.text_input("Group Name")
        
        notes = st.text_area("Notes/Observations")
        
        if st.button("Submit RTK Data"):
            # Here you could save to a database or Google Sheets
            st.success("Data recorded successfully!")
            st.json({
                "UID": point['UID'],
                "Map": point['MAP'],
                "Point": point['POINT'],
                "Student": student_name,
                "Group": group_name,
                "RTK_Lat": rtk_lat,
                "RTK_Lon": rtk_lon,
                "Notes": notes
            })

def show_admin_interface(df):
    """Show admin interface for generating QR codes"""
    st.header("Admin Interface")
    
    tab1, tab2, tab3 = st.tabs(["Generate QR Codes", "View All Data", "Instructions"])
    
    with tab1:
        st.subheader("Generate QR Codes for Field Deployment")
        # Get base URL
        base_url = st.text_input("Base URL", value="https://your-app.streamlit.app/")
        if st.button("Generate All QR Codes"):
            cols = st.columns(5)
            # Generate one QR per UID
            for idx, row in df.iterrows():
                uid = row['UID']
                point = row['POINT']
                map_name = row['MAP']
                # percent-encode UID to ensure scanners treat full string
                url = f"{base_url.rstrip('/')}?uid={quote(uid)}"
                
                # Generate QR code
                qr_img = generate_qr_code(url)
                
                # Arrange in columns
                col = cols[idx % len(cols)]
                with col:
                    st.image(qr_img, caption=f"{map_name} - Point {point}")
                    st.text(f"URL: {url}")
                     
                    # Download button for QR code
                    buffer = BytesIO()
                    qr_img.save(buffer, format='PNG')
                    st.download_button(
                        label=f"Download QR: UID {uid}",
                        data=buffer.getvalue(),
                        file_name=f"qr_uid_{uid}.png",
                        mime="image/png"
                    )
    
    with tab2:
        st.subheader("All Point Data")
        st.dataframe(df)
        
        # Option to download data
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name="geostatistics_data.csv",
            mime="text/csv"
        )
    
    with tab3:
        st.subheader("Setup Instructions")
        st.markdown("""
        ### How to use this system:
        
        1. **Deploy this app** to Streamlit Cloud (free)
        2. **Generate QR codes** using the "Generate QR Codes" tab
        3. **Print and laminate** the QR codes
        4. **Place QR codes** at corresponding field locations
        5. **Students scan** QR codes to view point data
        
        ### Deployment Steps:
        1. Upload this code to GitHub
        2. Go to [share.streamlit.io](https://share.streamlit.io)
        3. Connect your GitHub repository
        4. Deploy the app
        5. Use the deployed URL in the QR code generator
        
        ### Requirements file (requirements.txt):
        ```
        streamlit
        pandas
        qrcode[pil]
        pillow
        ```
        """)

if __name__ == "__main__":
    main()
