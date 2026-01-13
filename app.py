import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, timedelta

# Page Configuration
st.set_page_config(
    page_title="SkyCast Analytics",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for "Light Mode Friendly"
st.markdown("""
    <style>
    .stApp {
        background-color: #FAFAFA;
        color: #333333;
    }
    h1, h2, h3 {
        color: #2C3E50;
    }
    </style>
    """, unsafe_allow_html=True)

def get_lat_lon(city_name):
    """
    Fetch latitude and longitude for a given city name using Open-Meteo Geocoding API.
    """
    if not city_name:
        return None, None
    
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&language=en&format=json"
        response = requests.get(url)
        data = response.json()
        
        if "results" in data and len(data["results"]) > 0:
            result = data["results"][0]
            return result["latitude"], result["longitude"]
        else:
            return None, None
    except Exception as e:
        st.error(f"Error fetching location for {city_name}: {e}")
        return None, None

def fetch_weather_data(lat, lon, start_date, end_date):
    """
    Fetch historical max temperature data from Open-Meteo Archive API.
    """
    try:
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "daily": "temperature_2m_max",
            "timezone": "auto"
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if "daily" in data:
            df = pd.DataFrame({
                "Date": data["daily"]["time"],
                "Max Temp (°C)": data["daily"]["temperature_2m_max"]
            })
            return df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Error fetching weather data: {e}")
        return pd.DataFrame()

# Title and Description
st.title("🌤️ SkyCast Analytics")
st.markdown("Compare historical daily maximum temperatures between two cities.")

# Input Section
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    city_a = st.text_input("City A", value="New York")

with col2:
    city_b = st.text_input("City B", value="London")

with col3:
    # Default to last 30 days
    today = datetime.now().date()
    thirty_days_ago = today - timedelta(days=30)
    
    date_range = st.date_input(
        "Select Date Range",
        value=(thirty_days_ago, today),
        max_value=today
    )

# Validate Date Range
start_date = None
end_date = None

if isinstance(date_range, tuple):
    if len(date_range) == 2:
        start_date, end_date = date_range
    elif len(date_range) == 1:
        start_date = date_range[0]
        end_date = start_date 

if st.button("Compare Temperatures"):
    if not city_a or not city_b:
        st.warning("Please enter both City A and City B.")
    elif not start_date or not end_date:
        st.warning("Please select a valid date range.")
    else:
        with st.spinner("Fetching data..."):
            # Fetch coordinates
            lat_a, lon_a = get_lat_lon(city_a)
            lat_b, lon_b = get_lat_lon(city_b)
            
            if lat_a is None:
                st.error(f"Could not find location for '{city_a}'")
            elif lat_b is None:
                st.error(f"Could not find location for '{city_b}'")
            else:
                # Fetch Weather Data
                df_a = fetch_weather_data(lat_a, lon_a, start_date, end_date)
                df_b = fetch_weather_data(lat_b, lon_b, start_date, end_date)
                
                if not df_a.empty and not df_b.empty:
                    # Rename columns for merging/plotting
                    df_a = df_a.rename(columns={"Max Temp (°C)": f"{city_a} Max Temp (°C)"})
                    df_b = df_b.rename(columns={"Max Temp (°C)": f"{city_b} Max Temp (°C)"})
                    
                    # Merge DataFrames on Date
                    merged_df = pd.merge(df_a, df_b, on="Date", how="outer")
                    
                    # Create Tabs
                    tab1, tab2 = st.tabs(["📈 Temperature Chart", "📄 Raw Data"])
                    
                    with tab1:
                        # Reshape for Plotly (Long Format)
                        plot_df = merged_df.melt(id_vars=["Date"], var_name="City", value_name="Temperature (°C)")
                        
                        fig = px.line(
                            plot_df, 
                            x="Date", 
                            y="Temperature (°C)", 
                            color="City",
                            title=f"Daily Max Temperature: {city_a} vs {city_b}",
                            markers=True,
                            template="plotly_white"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                    with tab2:
                        st.dataframe(merged_df, use_container_width=True)
                else:
                    st.error("Could not retrieve weather data for one or both cities.")
