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
@st.cache_data
def load_data():
    data = {
        'PointID': [1, 2, 3, 4, 5],
        'Latitude': [-31.9505, -31.9510, -31.9515, -31.9520, -31.9525],
        'Longitude': [115.8605, 115.8610, 115.8615, 115.8620, 115.8625],
        'Clay_percent': [20.5, 18.2, 22.1, 19.8, 21.3],
        'P_ppm': [25, 30, 20, 35, 28],
        'K_ppm': [180, 165, 195, 170, 185],
        'NDVI': [0.65, 0.72, 0.58, 0.68, 0.63],
        'pH': [6.2, 6.8, 6.1, 6.5, 6.3]
    }
    return pd.DataFrame(data)

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
        # Show admin interface
        show_admin_interface(df)

def show_point_detail(point):
    """Display detailed information for a specific point"""
    st.header(f"Point {point['PointID']} - Field Data")
    
    # Create columns for better layout
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Location", f"{point['Latitude']:.4f}, {point['Longitude']:.4f}")
        st.metric("Clay %", f"{point['Clay_percent']}%")
    
    with col2:
        st.metric("P (ppm)", f"{point['P_ppm']} ppm")
        st.metric("K (ppm)", f"{point['K_ppm']} ppm")
    
    with col3:
        st.metric("NDVI", f"{point['NDVI']:.2f}")
        st.metric("pH", f"{point['pH']:.1f}")
    
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
        
        if st.button("Generate All QR Codes"):
            cols = st.columns(3)
            
            for index, (_, row) in enumerate(df.iterrows()):
                point_id = row['PointID']
                url = f"{base_url}?point={point_id}"
                
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
