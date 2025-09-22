import streamlit as st
import json
import tempfile
import os
import pandas as pd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import ee
from earth_engine_utils import initialize_earth_engine, get_admin_boundaries, get_boundary_names
from vegetation_indices import mask_clouds, add_vegetation_indices

# Custom CSS for modern dark GIS dashboard
st.markdown("""
<style>
    /* Modern Dark GIS Dashboard Theme */
    :root {
        --primary-bg: #0a0f1c;
        --secondary-bg: #1a1f2e;
        --tertiary-bg: #2a2f3e;
        --accent-primary: #00d4ff;
        --accent-secondary: #ff6b6b;
        --accent-tertiary: #4ecdc4;
        --text-primary: #ffffff;
        --text-secondary: #b0b3b8;
        --text-muted: #6c757d;
        --success: #00ff88;
        --warning: #ffaa00;
        --danger: #ff4444;
        --gradient-bg: linear-gradient(135deg, #0a0f1c 0%, #1a1f2e 50%, #0a0f1c 100%);
        --gradient-accent: linear-gradient(90deg, #00d4ff 0%, #4ecdc4 100%);
        --gradient-card: linear-gradient(135deg, #1a1f2e 0%, #2a2f3e 100%);
        --shadow-glow: 0 0 20px rgba(0, 212, 255, 0.3);
    }

    /* Main container styling */
    .stApp {
        background: var(--gradient-bg);
        color: var(--text-primary);
    }

    /* Sidebar styling */
    .css-1d391kg {
        background: var(--secondary-bg) !important;
        border-right: 1px solid var(--tertiary-bg);
    }

    .sidebar-header {
        background: var(--gradient-accent);
        padding: 1.5rem 1rem;
        text-align: center;
        margin-bottom: 1rem;
        border-radius: 0 0 15px 15px;
    }

    .sidebar-title {
        color: white;
        font-size: 1.5rem;
        font-weight: 800;
        margin: 0;
    }

    .sidebar-subtitle {
        color: rgba(255,255,255,0.9);
        font-size: 0.8rem;
        margin: 0;
    }

    /* Button styling */
    .stButton button {
        background: var(--gradient-accent);
        color: white;
        border: none;
        padding: 0.7rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
        margin: 0.2rem 0;
    }

    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-glow);
    }

    /* Selectbox styling */
    .stSelectbox label {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }

    .stSelectbox div[data-baseweb="select"] {
        background: var(--tertiary-bg) !important;
        border: 1px solid var(--accent-primary) !important;
        border-radius: 8px !important;
    }

    /* Date input styling */
    .stDateInput label {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }

    .stDateInput div[data-baseweb="input"] {
        background: var(--tertiary-bg) !important;
        border: 1px solid var(--accent-primary) !important;
        border-radius: 8px !important;
    }

    /* Checkbox styling */
    .stCheckbox label {
        color: var(--text-primary) !important;
    }

    /* Slider styling */
    .stSlider label {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }

    /* Map container styling */
    .map-container {
        border: 2px solid var(--accent-primary);
        border-radius: 15px;
        overflow: hidden;
        box-shadow: var(--shadow-glow);
        margin: 1rem 0;
    }

    /* Status indicators */
    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin: 0.2rem;
        background: var(--tertiary-bg);
        border: 1px solid var(--accent-primary);
    }

    .status-connected {
        background: rgba(0, 255, 136, 0.2);
        border-color: var(--success);
        color: var(--success);
    }

    .status-disconnected {
        background: rgba(255, 68, 68, 0.2);
        border-color: var(--danger);
        color: var(--danger);
    }

    /* Card styling */
    .info-card {
        background: var(--gradient-card);
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid var(--tertiary-bg);
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }

    .info-card h3 {
        color: var(--accent-primary);
        margin-top: 0;
        border-bottom: 2px solid var(--accent-primary);
        padding-bottom: 0.5rem;
    }

    /* Landing page styling */
    .landing-header {
        background: var(--gradient-bg);
        padding: 4rem 2rem;
        text-align: center;
        border-radius: 20px;
        margin: 2rem 0;
        position: relative;
        overflow: hidden;
    }

    .landing-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: radial-gradient(circle at 20% 80%, rgba(0, 212, 255, 0.1) 0%, transparent 50%),
                   radial-gradient(circle at 80% 20%, rgba(78, 205, 196, 0.1) 0%, transparent 50%);
    }

    .landing-title {
        font-size: 4rem;
        font-weight: 800;
        background: var(--gradient-accent);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
        position: relative;
    }

    .landing-subtitle {
        font-size: 1.3rem;
        color: var(--text-secondary);
        margin-bottom: 2rem;
        max-width: 600px;
        margin-left: auto;
        margin-right: auto;
        position: relative;
    }

    /* Button group styling */
    .button-group {
        display: flex;
        gap: 1rem;
        justify-content: center;
        margin: 2rem 0;
    }

    /* Feature grid */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }

    .feature-item {
        background: var(--gradient-card);
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        border: 1px solid var(--tertiary-bg);
        transition: transform 0.3s ease;
    }

    .feature-item:hover {
        transform: translateY(-5px);
        border-color: var(--accent-primary);
    }

    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }

    /* Top bar styling */
    .top-bar {
        background: var(--secondary-bg);
        padding: 1rem 2rem;
        border-radius: 0 0 15px 15px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
        border-bottom: 3px solid var(--accent-primary);
    }

    .platform-title {
        font-size: 1.8rem;
        font-weight: 800;
        background: var(--gradient-accent);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .action-buttons {
        display: flex;
        gap: 1rem;
    }

    /* NDVI Legend */
    .ndvi-legend {
        background: var(--gradient-card);
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid var(--accent-primary);
        position: absolute;
        bottom: 20px;
        right: 20px;
        z-index: 1000;
    }

    .legend-title {
        color: var(--accent-primary);
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    .legend-color {
        width: 20px;
        height: 20px;
        border-radius: 3px;
        margin-right: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Page configuration
st.set_page_config(
    page_title="Khisba GIS Platform",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'current_page' not in st.session_state:
    st.session_state.current_page = "landing"
if 'ee_initialized' not in st.session_state:
    st.session_state.ee_initialized = False
if 'credentials_uploaded' not in st.session_state:
    st.session_state.credentials_uploaded = False
if 'selected_geometry' not in st.session_state:
    st.session_state.selected_geometry = None
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None

# Landing Page
if not st.session_state.authenticated:
    st.markdown("""
    <div class="landing-header">
        <h1 class="landing-title">🌍 KHISBA GIS</h1>
        <p class="landing-subtitle">Advanced Geospatial Intelligence Platform Powered by Google Earth Engine</p>
        
        <div style="display: flex; justify-content: center; margin: 2rem 0;">
            <div style="width: 150px; height: 150px; background: conic-gradient(from 0deg, #00d4ff, #4ecdc4, #00d4ff); 
                        border-radius: 50%; animation: rotate 10s linear infinite; box-shadow: 0 0 50px rgba(0, 212, 255, 0.5);"></div>
        </div>
        
        <div class="button-group">
            <button onclick="window.streamlitSessionState.set({authenticated: true, current_page: 'dashboard'})" 
                    style="background: var(--gradient-accent); color: white; border: none; padding: 1rem 2rem; 
                           border-radius: 10px; font-size: 1.1rem; font-weight: 600; cursor: pointer; 
                           transition: all 0.3s ease;">
                🚀 Launch Platform
            </button>
            <button style="background: transparent; color: var(--accent-primary); border: 2px solid var(--accent-primary); 
                          padding: 1rem 2rem; border-radius: 10px; font-size: 1.1rem; font-weight: 600; cursor: pointer;">
                ℹ️ Learn More
            </button>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Features section
    st.markdown("""
    <div style="text-align: center; margin: 3rem 0;">
        <h2 style="color: var(--accent-primary); font-size: 2.5rem; margin-bottom: 1rem;">Platform Features</h2>
        <p style="color: var(--text-secondary); font-size: 1.2rem;">Advanced geospatial analytics for informed decision-making</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-item">
            <div class="feature-icon">🌿</div>
            <h3>Vegetation Analytics</h3>
            <p>Comprehensive analysis of 40+ vegetation indices with scientific precision</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-item">
            <div class="feature-icon">💧</div>
            <h3>Water Resources</h3>
            <p>Advanced water indices monitoring and management capabilities</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-item">
            <div class="feature-icon">📊</div>
            <h3>Multi-scale Analysis</h3>
            <p>From field-level to continental scale with intelligent processing</p>
        </div>
        """, unsafe_allow_html=True)

    # Authentication section (hidden behind Learn More)
    with st.expander("🔐 Platform Access", expanded=False):
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <h3 style="color: var(--accent-primary);">Enterprise Authentication</h3>
            <p style="color: var(--text-secondary);">Enter admin credentials to access the platform</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            password = st.text_input("**Admin Password**", type="password", 
                                   placeholder="Enter admin password", 
                                   help="Demo password: admin")
            
            if st.button("🔓 **Authenticate**", type="primary", use_container_width=True):
                if password == "admin":
                    st.session_state.authenticated = True
                    st.session_state.current_page = "dashboard"
                    st.rerun()
                else:
                    st.error("❌ Invalid password. Demo password: admin")

    st.stop()

# Main Dashboard after authentication
st.markdown("""
<div class="top-bar">
    <div>
        <span class="platform-title">Khisba GIS Platform</span>
        <span class="status-badge status-connected">Earth Engine Connected</span>
    </div>
    <div class="action-buttons">
        <button>⬇ Export Data</button>
        <button>🔒 Logout</button>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar with modern styling
st.sidebar.markdown("""
<div class="sidebar-header">
    <h2 class="sidebar-title">🌍 KHISBA</h2>
    <p class="sidebar-subtitle">Geospatial Intelligence Dashboard</p>
</div>
""", unsafe_allow_html=True)

# Authentication status
st.sidebar.markdown("### 🔐 Authentication Status")
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.session_state.ee_initialized:
        st.markdown('<span class="status-badge status-connected">GEE Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-disconnected">GEE Disconnected</span>', unsafe_allow_html=True)

# Google Earth Engine Authentication
if not st.session_state.ee_initialized:
    st.sidebar.markdown("""
    <div class="info-card">
        <h3>🔑 GEE Credentials</h3>
        <p>Upload your service account JSON file to initialize Earth Engine</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.sidebar.file_uploader(
        "**Choose service account JSON file**",
        type=['json'],
        help="Upload your Google Earth Engine service account JSON credentials"
    )
    
    if uploaded_file is not None:
        try:
            credentials_data = json.load(uploaded_file)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
                json.dump(credentials_data, tmp_file)
                credentials_path = tmp_file.name
            
            success = initialize_earth_engine(credentials_path)
            
            if success:
                st.session_state.ee_initialized = True
                st.session_state.credentials_uploaded = True
                st.sidebar.success("✅ Earth Engine initialized successfully!")
                os.unlink(credentials_path)
                st.rerun()
            else:
                st.sidebar.error("❌ Failed to initialize Earth Engine")
                
        except Exception as e:
            st.sidebar.error(f"❌ Error processing credentials: {str(e)}")

# Main dashboard content
if st.session_state.ee_initialized:
    # Study Area Selection in Sidebar
    st.sidebar.markdown("### 🗺️ Study Area Selection")
    
    # Administrative level dropdown
    admin_level = st.sidebar.selectbox(
        "**Administrative Level**",
        ["Country", "State/Province", "Municipality"],
        help="Select the administrative level for analysis"
    )
    
    # Region selection based on level
    try:
        countries_fc = get_admin_boundaries(0)
        if countries_fc is not None:
            country_names = get_boundary_names(countries_fc, 0)
            selected_country = st.sidebar.selectbox(
                "**Select Country**",
                options=[""] + country_names,
                help="Choose a country for analysis"
            )
        else:
            st.sidebar.error("Failed to load countries data")
            selected_country = ""
    except Exception as e:
        st.sidebar.error(f"Error loading countries: {str(e)}")
        selected_country = ""

    # Admin1 selection
    selected_admin1 = ""
    if selected_country and admin_level in ["State/Province", "Municipality"]:
        try:
            country_feature = countries_fc.filter(ee.Filter.eq('ADM0_NAME', selected_country)).first()
            country_code = country_feature.get('ADM0_CODE').getInfo()
            
            admin1_fc = get_admin_boundaries(1, country_code)
            if admin1_fc is not None:
                admin1_names = get_boundary_names(admin1_fc, 1)
                selected_admin1 = st.sidebar.selectbox(
                    "**Select State/Province**",
                    options=[""] + admin1_names,
                    help="Choose a state or province"
                )
        except Exception as e:
            st.sidebar.error(f"Error loading admin1: {str(e)}")

    # Admin2 selection
    selected_admin2 = ""
    if selected_admin1 and admin_level == "Municipality":
        try:
            admin1_feature = admin1_fc.filter(ee.Filter.eq('ADM1_NAME', selected_admin1)).first()
            admin1_code = admin1_feature.get('ADM1_CODE').getInfo()
            
            admin2_fc = get_admin_boundaries(2, None, admin1_code)
            if admin2_fc is not None:
                admin2_names = get_boundary_names(admin2_fc, 2)
                selected_admin2 = st.sidebar.selectbox(
                    "**Select Municipality**",
                    options=[""] + admin2_names,
                    help="Choose a municipality"
                )
        except Exception as e:
            st.sidebar.error(f"Error loading admin2: {str(e)}")

    # Date range selector
    st.sidebar.markdown("### 📅 Date Range")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input(
            "**Start Date**",
            value=datetime(2023, 1, 1)
        )
    with col2:
        end_date = st.date_input(
            "**End Date**",
            value=datetime(2023, 12, 31)
        )

    # Vegetation indices checkboxes
    st.sidebar.markdown("### 🌿 Vegetation Indices")
    available_indices = [
        'NDVI', 'ARVI', 'ATSAVI', 'DVI', 'EVI', 'EVI2', 'GNDVI', 'MSAVI', 'MSI', 'MTVI', 'MTVI2',
        'NDTI', 'NDWI', 'OSAVI', 'RDVI', 'RI', 'RVI', 'SAVI', 'TVI', 'TSAVI', 'VARI', 'VIN', 'WDRVI',
        'GCVI', 'AWEI', 'MNDWI', 'WI', 'ANDWI', 'NDSI', 'nDDI', 'NBR', 'DBSI', 'SI', 'S3', 'BRI',
        'SSI', 'NDSI_Salinity', 'SRPI', 'MCARI', 'NDCI', 'PSSRb1', 'SIPI', 'PSRI', 'Chl_red_edge', 'MARI', 'NDMI'
    ]
    
    selected_indices = []
    cols = st.sidebar.columns(2)
    for i, index in enumerate(available_indices):
        with cols[i % 2]:
            if st.checkbox(index, value=index in ['NDVI', 'EVI', 'SAVI', 'NDWI']):
                selected_indices.append(index)

    # Main content area
    if selected_country:
        # Interactive Map Section
        st.markdown("""
        <div style="margin: 2rem 0;">
            <h2 style="color: var(--accent-primary); border-bottom: 2px solid var(--accent-primary); 
                       padding-bottom: 0.5rem;">Interactive GIS Map</h2>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            # Determine geometry based on selection
            if selected_admin2 and admin_level == "Municipality" and 'admin2_fc' in locals():
                geometry = admin2_fc.filter(ee.Filter.eq('ADM2_NAME', selected_admin2))
                area_name = f"{selected_admin2}, {selected_admin1}, {selected_country}"
            elif selected_admin1 and admin_level in ["State/Province", "Municipality"] and 'admin1_fc' in locals():
                geometry = admin1_fc.filter(ee.Filter.eq('ADM1_NAME', selected_admin1))
                area_name = f"{selected_admin1}, {selected_country}"
            else:
                geometry = countries_fc.filter(ee.Filter.eq('ADM0_NAME', selected_country))
                area_name = selected_country
            
            bounds = geometry.geometry().bounds().getInfo()
            coords = bounds['coordinates'][0]
            lats = [coord[1] for coord in coords]
            lons = [coord[0] for coord in coords]
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)
            
            # Create modern map
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=6,
                tiles='CartoDB dark_matter',
                control_scale=True
            )
            
            # Add study area boundary
            folium.GeoJson(
                bounds,
                style_function=lambda x: {
                    'fillColor': '#00d4ff',
                    'color': '#ffffff',
                    'weight': 3,
                    'fillOpacity': 0.1,
                    'dashArray': '5, 5'
                },
                popup=folium.Popup(f"<b>Study Area:</b><br>{area_name}", max_width=300)
            ).add_to(m)
            
            # Add NDVI legend
            st.markdown("""
            <div class="ndvi-legend">
                <div class="legend-title">NDVI Scale</div>
                <div style="display: flex; align-items: center; margin: 0.2rem 0;">
                    <div class="legend-color" style="background: #d73027;"></div>
                    <span>Water/Barren (-1 to 0)</span>
                </div>
                <div style="display: flex; align-items: center; margin: 0.2rem 0;">
                    <div class="legend-color" style="background: #f46d43;"></div>
                    <span>Low Vegetation (0 to 0.2)</span>
                </div>
                <div style="display: flex; align-items: center; margin: 0.2rem 0;">
                    <div class="legend-color" style="background: #fdae61;"></div>
                    <span>Moderate (0.2 to 0.5)</span>
                </div>
                <div style="display: flex; align-items: center; margin: 0.2rem 0;">
                    <div class="legend-color" style="background: #a6d96a;"></div>
                    <span>High (0.5 to 0.8)</span>
                </div>
                <div style="display: flex; align-items: center; margin: 0.2rem 0;">
                    <div class="legend-color" style="background: #1a9850;"></div>
                    <span>Dense (0.8 to 1)</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Display map
            st.markdown('<div class="map-container">', unsafe_allow_html=True)
            st_folium(m, width=None, height=500, key="gis_map")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.session_state.selected_geometry = geometry
            
            # Analysis controls
            col1, col2, col3 = st.columns([2, 1, 1])
            with col2:
                collection_choice = st.selectbox(
                    "**Satellite Collection**",
                    options=["Sentinel-2", "Landsat-8"]
                )
            with col3:
                cloud_cover = st.slider("**Cloud Cover %**", 0, 100, 20)
            
            if st.button("🚀 **Run Geospatial Analysis**", type="primary", use_container_width=True):
                if not selected_indices:
                    st.error("Please select at least one vegetation index")
                else:
                    with st.spinner("Processing satellite data..."):
                        try:
                            if collection_choice == "Sentinel-2":
                                collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                            else:
                                collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
                            
                            filtered_collection = (collection
                                .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
                                .filterBounds(st.session_state.selected_geometry)
                                .filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', cloud_cover))
                            )
                            
                            if collection_choice == "Sentinel-2":
                                processed_collection = (filtered_collection
                                    .map(mask_clouds)
                                    .map(add_vegetation_indices)
                                )
                            else:
                                processed_collection = filtered_collection.map(add_vegetation_indices)
                            
                            results = {}
                            for index in selected_indices:
                                try:
                                    def add_date_and_reduce(image):
                                        reduced = image.select(index).reduceRegion(
                                            reducer=ee.Reducer.mean(),
                                            geometry=st.session_state.selected_geometry.geometry(),
                                            scale=30,
                                            maxPixels=1e9
                                        )
                                        return ee.Feature(None, reduced.set('date', image.date().format()))
                                    
                                    time_series = processed_collection.map(add_date_and_reduce)
                                    time_series_list = time_series.getInfo()
                                    
                                    dates = []
                                    values = []
                                    
                                    if 'features' in time_series_list:
                                        for feature in time_series_list['features']:
                                            props = feature['properties']
                                            if index in props and props[index] is not None and 'date' in props:
                                                dates.append(props['date'])
                                                values.append(props[index])
                                    
                                    results[index] = {'dates': dates, 'values': values}
                                    
                                except Exception as e:
                                    st.warning(f"Could not calculate {index}: {str(e)}")
                                    results[index] = {'dates': [], 'values': []}
                            
                            st.session_state.analysis_results = results
                            st.success("✅ Analysis completed successfully!")
                            
                        except Exception as e:
                            st.error(f"❌ Analysis failed: {str(e)}")
            
        except Exception as e:
            st.error(f"❌ Map Error: {str(e)}")

# Display Results
if st.session_state.analysis_results:
    st.markdown("""
    <div style="margin: 3rem 0;">
        <h2 style="color: var(--accent-primary); border-bottom: 2px solid var(--accent-primary); 
                   padding-bottom: 0.5rem;">Analysis Results</h2>
    </div>
    """, unsafe_allow_html=True)
    
    results = st.session_state.analysis_results
    
    # Summary statistics
    summary_data = []
    for index, data in results.items():
        if data['values']:
            values = [v for v in data['values'] if v is not None]
            if values:
                summary_data.append({
                    'Index': index,
                    'Mean': round(sum(values) / len(values), 4),
                    'Min': round(min(values), 4),
                    'Max': round(max(values), 4),
                    'Count': len(values)
                })
    
    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True)
    
    # Charts
    indices_to_plot = st.multiselect(
        "**Select indices to visualize:**",
        options=list(results.keys()),
        default=list(results.keys())[:4] if len(results) >= 4 else list(results.keys())
    )
    
    if indices_to_plot:
        for index in indices_to_plot:
            data = results[index]
            if data['dates'] and data['values']:
                try:
                    dates = [datetime.fromisoformat(d.replace('Z', '+00:00')) for d in data['dates']]
                    values = [v for v in data['values'] if v is not None]
                    
                    if dates and values and len(dates) == len(values):
                        df = pd.DataFrame({'Date': dates, 'Value': values})
                        df = df.sort_values('Date')
                        
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=df['Date'], 
                            y=df['Value'],
                            mode='lines',
                            name=f'{index}',
                            line=dict(color='#00d4ff', width=3)
                        ))
                        
                        fig.update_layout(
                            title=f'{index} Time Series',
                            plot_bgcolor='#0a0f1c',
                            paper_bgcolor='#0a0f1c',
                            font=dict(color='white'),
                            xaxis=dict(gridcolor='#1a1f2e'),
                            yaxis=dict(gridcolor='#1a1f2e'),
                            height=400
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                except Exception as e:
                    st.error(f"Error creating chart for {index}: {str(e)}")

# Footer
st.markdown("""
<div style="text-align: center; margin-top: 4rem; padding: 2rem; background: var(--secondary-bg); 
            border-radius: 10px; border-top: 3px solid var(--accent-primary);">
    <p style="color: var(--text-secondary); margin: 0;">
        🌍 <strong>Khisba GIS Platform</strong> • Advanced Geospatial Intelligence • Powered by Google Earth Engine
    </p>
</div>
""", unsafe_allow_html=True)
