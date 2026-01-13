import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta

# --- Configuration ---
st.set_page_config(page_title="SkyCast Analytics", page_icon="🌤️", layout="wide")

# --- Helper Functions ---
@st.cache_data
def get_city_coordinates(city_name):
    """
    Fetches coordinates (lat, lon) for a given city name using Open-Meteo Geocoding API.
    """
    if not city_name:
        return None
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city_name, "count": 1, "language": "en", "format": "json"}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if "results" in data and data["results"]:
            return data["results"][0]
        else:
            return None
    except Exception as e:
        st.error(f"Error fetching coordinates for {city_name}: {e}")
        return None

@st.cache_data
def get_historical_weather(lat, lon, start_date, end_date):
    """
    Fetches historical daily max temperature from Open-Meteo Archive API.
    """
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "daily": "temperature_2m_max",
        "timezone": "auto"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if "daily" in data:
            df = pd.DataFrame({
                "Date": data["daily"]["time"],
                "Max Temp (°C)": data["daily"]["temperature_2m_max"]
            })
            df["Date"] = pd.to_datetime(df["Date"])
            return df
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching weather data: {e}")
        return pd.DataFrame()

# --- UI Layout ---
st.title("SkyCast Analytics 🌤️")
st.markdown("Compare historical temperature data between two cities.")

# Input Section
col1, col2 = st.columns(2)
with col1:
    city_a = st.text_input("City A", value="London", placeholder="Enter City A")
with col2:
    city_b = st.text_input("City B", value="New York", placeholder="Enter City B")

today = datetime.today()
default_start = today - timedelta(days=30)
date_range = st.date_input(
    "Date Range",
    value=(default_start, today),
    max_value=today
)

if len(date_range) == 2:
    start_date, end_date = date_range
    
    if st.button("Generate Comparison", type="primary"):
        with st.spinner("Fetching data..."):
            # Fetch coordinates
            coords_a = get_city_coordinates(city_a)
            coords_b = get_city_coordinates(city_b)
            
            if coords_a and coords_b:
                # Fetch weather data
                df_a = get_historical_weather(coords_a["latitude"], coords_a["longitude"], start_date, end_date)
                df_b = get_historical_weather(coords_b["latitude"], coords_b["longitude"], start_date, end_date)
                
                if not df_a.empty and not df_b.empty:
                    # Calculate Metrics
                    avg_a = df_a["Max Temp (°C)"].mean()
                    avg_b = df_b["Max Temp (°C)"].mean()
                    
                    # Display Metrics
                    st.divider()
                    m_col1, m_col2 = st.columns(2)
                    m_col1.metric(f"📍 {city_a} Avg Max Temp", f"{avg_a:.1f}°C")
                    m_col2.metric(f"📍 {city_b} Avg Max Temp", f"{avg_b:.1f}°C")
                    st.divider()

                    # Combine data
                    df_a["City"] = city_a
                    df_b["City"] = city_b
                    df_combined = pd.concat([df_a, df_b])
                    
                    # Visualization Tab
                    tab1, tab2 = st.tabs(["📈 Chart", "📄 Data Table"])
                    
                    with tab1:
                        # Custom Colors: Neon Blue & Sunset Orange
                        color_map = {city_a: "#00E5FF", city_b: "#FF4500"}
                        
                        fig = px.line(
                            df_combined, 
                            x="Date", 
                            y="Max Temp (°C)", 
                            color="City",
                            title=f"Max Daily Temperature: {city_a} vs {city_b}",
                            markers=True,
                            color_discrete_map=color_map
                        )
                        fig.update_layout(
                            xaxis_title="Date", 
                            yaxis_title="Temperature (°C)",
                            legend_title="City",
                            hovermode="x unified"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with tab2:
                        st.dataframe(df_combined, use_container_width=True)
                else:
                    st.warning("No weather data found for the selected range.")
            else:
                if not coords_a:
                    st.error(f"Could not find city: {city_a}")
                if not coords_b:
                    st.error(f"Could not find city: {city_b}")
else:
    st.info("Please select a complete date range.")
