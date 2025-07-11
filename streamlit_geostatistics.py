import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
import base64
from PIL import Image

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
        # read full CSV then drop Latitude/Longitude columns
        df = pd.read_csv("data/points.csv")
        df = df.drop(columns=["Latitude", "Longitude"], errors="ignore")
        return df
    except FileNotFoundError:
        st.error("Data file not found: data/points.csv. Please add your 43-point CSV.")
        return pd.DataFrame()

def generate_qr_code(url):
    """Generate QR code for a given URL"""
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
    
    # URL parameters to show specific point
    query_params = st.experimental_get_query_params()
    
    if 'point' in query_params:
        # Show specific point data
        try:
            point_id = int(query_params['point'][0])
            point_data = df[df['PointID'] == point_id]
            
            if not point_data.empty:
                show_point_detail(point_data.iloc[0])
            else:
                st.error(f"Point {point_id} not found")
        except ValueError:
            st.error("Invalid point ID")
    else:
        # Password-protected admin interface
        # Define admin password (replace or use st.secrets)
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
    """Display detailed information for a specific point"""
    st.header(f"Point {point['PointID']} - Field Data")
    
    # get optional parameter filter
    query_params = st.experimental_get_query_params()
    selected_param = query_params.get("param", [None])[0]
    # show either all metrics or only the selected one
    if not selected_param or selected_param == "All":
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Clay %", f"{point['Clay_percent']}%")
            st.metric("P (ppm)", f"{point['P_ppm']} ppm")
        with col2:
            st.metric("K (ppm)", f"{point['K_ppm']} ppm")
            st.metric("NDVI", f"{point['NDVI']:.2f}")
        with col3:
            st.metric("pH", f"{point['pH']:.1f}")
    else:
        # display only the requested parameter
        label = selected_param.replace("_", " ")
        value = point[selected_param]
        if selected_param == "NDVI":
            fmt = f"{value:.2f}"
        elif selected_param == "pH":
            fmt = f"{value:.1f}"
        elif selected_param == "Clay_percent":
            fmt = f"{value}%"
        else:
            fmt = f"{value}"
        st.metric(label, fmt)
    
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
                "Point": point['PointID'],
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
        # Select parameter for this map
        param = st.selectbox("Select parameter (or All)", ["All", "Clay_percent", "P_ppm", "K_ppm", "NDVI", "pH"])
        
        if st.button("Generate All QR Codes"):
            cols = st.columns(3)
            
            for index, (_, row) in enumerate(df.iterrows()):
                point_id = row['PointID']
                # construct URL with optional parameter
                if param == "All":
                    url = f"{base_url}?point={point_id}"
                else:
                    url = f"{base_url}?point={point_id}&param={param}"
                
                # Generate QR code
                qr_img = generate_qr_code(url)
                
                # Display in columns
                col_idx = index % 3
                with cols[col_idx]:
                    st.image(qr_img, caption=f"Point {point_id}")
                    st.text(f"URL: {url}")
                    
                    # Download button for QR code
                    buffer = BytesIO()
                    qr_img.save(buffer, format='PNG')
                    st.download_button(
                        label=f"Download QR Code {point_id}",
                        data=buffer.getvalue(),
                        file_name=f"point_{point_id}_qr.png",
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
