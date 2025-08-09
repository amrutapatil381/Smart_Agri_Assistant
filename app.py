import streamlit as st
import pandas as pd
import numpy as np
import pickle
import requests
import plotly.express as px
import sqlite3
from datetime import datetime
import geocoder
from geopy.distance import geodesic
import openai


# Load dataset
data = pd.read_csv(r"D:\ABC\Sample\crop_data.csv")

# Load model
def load_model():
    with open(r"D:\ABC\Sample\crop_model.pkl", "rb") as f:
        return pickle.load(f)

model = load_model()
# OpenAI Chatbot API (More Reliable)



# Function to get current weather
def get_weather():
    API_KEY = "d8daff33beb045e1a84124758250204"  # Ensure no trailing spaces
    user_location = geocoder.ip('me')
    if user_location.latlng:
        lat, lon= user_location.latlng
        url = f"https://api.weatherapi.com/v1/current.json?key={API_KEY}&q={lat},{lon}"
    else:
        url = f"https://api.weatherapi.com/v1/current.json?key={API_KEY}&q=India"

    try:
        response = requests.get(url, timeout=10)  # 10-second timeout
        response.raise_for_status()  # Raise an error if the request fails
        weather = response.json()
        return weather['current']['temp_c'], weather['current']['humidity']
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Weather API Error: {e}")  # Show error in Streamlit
        return None, None
 

# Test the function
temperature, humidity = get_weather()
if temperature and humidity:
    st.write(f"🌡️ Temperature: {temperature}°C, 💧 Humidity: {humidity}%")
else:
    st.write("⚠️ Failed to fetch live weather. Using default values.")

# Function to get 7-day weather forecast
def get_weather_forecast():
    API_KEY = "d8daff33beb045e1a84124758250204"  # Ensure no trailing spaces
    url = f"https://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q=India&days=7"

    try:
        response = requests.get(url, timeout=10)  # 10-second timeout
        response.raise_for_status()  # Raise an error if the request fails
        forecast = response.json()
        return forecast['forecast']['forecastday']
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Weather API Error: {e}")  # Show error in Streamlit
        return None

# Database Connection
conn = sqlite3.connect("crop_recommendations.db")
c = conn.cursor()
c.execute("""
    CREATE TABLE IF NOT EXISTS predictions 
    (id INTEGER PRIMARY KEY, nitrogen REAL, phosphorus REAL, potassium REAL, pH REAL, rainfall REAL, crop TEXT, timestamp TEXT)
""")
conn.commit()


# Smart Reminders Function
def get_farming_reminders(crop):
    current_month = datetime.now().month
    st.write(f"📅 Current month: {current_month}")  # Debugging

    crop_calendar = {
        "rice": {"sow": [6, 7], "harvest": [10, 11]},
        "maize": {"sow": [5, 6, 7], "harvest": [9, 10, 11]},
        "chickpea": {"sow": [10, 11], "harvest": [2, 3, 4]},
        "wheat": {"sow": [11, 12], "harvest": [4, 5]},
        "sugarcane": {"sow": [2, 3, 4], "harvest": [10, 11, 12]},
    }

    crop = crop.lower()
    if crop in crop_calendar:
        reminders = []
        if current_month in crop_calendar[crop]["sow"]:
            reminders.append(f"🌱 It's the best time to sow {crop}!")
        if current_month in crop_calendar[crop]["harvest"]:
            reminders.append(f"🌾 It's time to harvest your {crop} crop!")
        return reminders

    return ["🚜 No farming reminders found for this crop."]

# Function to add tasks
conn = sqlite3.connect("farm_management.db")
c = conn.cursor()

# Create tables for farm management

c.execute("""
    CREATE TABLE IF NOT EXISTS weather_alerts (
        id INTEGER PRIMARY KEY, 
        alert TEXT, 
        date TEXT
    )
""")
conn.commit()


# Advanced Weather Alerts
def get_extended_weather():
    API_KEY = "d8daff33beb045e1a84124758250204"
    url = f"https://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q=India&days=14"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        forecast = response.json()
        return forecast['forecast']['forecastday']
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Weather API Error: {e}")
        return None

# Function to check weather alerts
def check_weather_alerts():
    forecast = get_extended_weather()
    alerts = []
    for day in forecast:
        date = day['date']
        temp = day['day']['avgtemp_c']
        conditions = day['day']['condition']['text']
        if temp > 40:
            alerts.append((date, "⚠️ Heatwave Alert! Temperatures exceeding 40°C."))
        if "rain" in conditions.lower():
            alerts.append((date, "⛈️ Heavy Rain Alert!"))
    
    # Store alerts in database
    for alert in alerts:
        c.execute("INSERT INTO weather_alerts (alert, date) VALUES (?, ?)", alert)
    conn.commit()
    return alerts

# Sidebar for Task Management


# Display Weather Alerts
st.sidebar.title("⛈️ Weather Alerts")
alerts = check_weather_alerts()
if alerts:
    for alert in alerts:
        st.sidebar.warning(f"{alert[1]} ({alert[0]})")
else:
    st.sidebar.info("✅ No extreme weather conditions detected.")

# Sidebar for Nearest Agricultural Shop
st.sidebar.title("📍 Nearest Agricultural Shop")

# Get user location
st.sidebar.write("Fetching your location... ⏳")
user_location = geocoder.ip('me')  # Get user's approximate location

if user_location.latlng:
    user_lat, user_lon = user_location.latlng
    st.sidebar.success(f"✅ Your Location: {user_lat}, {user_lon}")

    # Predefined Agri Shops (Lat, Lon, Name)
    agri_shops = [
        (28.7041, 77.1025, "Krishi Kendra, Delhi"),
        (19.0760, 72.8777, "Agri Fertilizer Hub, Mumbai"),
        (12.9716, 77.5946, "Green Grow, Bangalore"),
        (22.5726, 88.3639, "Farm Supply, Kolkata"),
        (13.0827, 80.2707, "Tamil Nadu Agri Store, Chennai"),
    ]

    # Find the nearest shop
    nearest_shop = min(agri_shops, key=lambda shop: geodesic((user_lat, user_lon), (shop[0], shop[1])).km)
    shop_name = nearest_shop[2]
    shop_distance = geodesic((user_lat, user_lon), (nearest_shop[0], nearest_shop[1])).km

    st.sidebar.info(f"🏪 Nearest Agri Shop: **{shop_name}**")
    st.sidebar.write(f"📍 Distance: **{shop_distance:.2f} km**")

else:
    st.sidebar.error("⚠️ Unable to fetch location. Please check your internet or allow location access.")

st.title(" Smart Agri Assistant")
tabs = st.tabs(["Crop Recommendation", "Fertilizer Advice", "Weather Forecast"])

with tabs[0]:
    st.title(" Crop Recommendation System")
    st.write("Enter soil parameters to get the best crop recommendation.")

    # User Input Fields
    N = st.number_input("Nitrogen (N)", min_value=0, max_value=200, value=50)
    P = st.number_input("Phosphorus (P)", min_value=0, max_value=200, value=50)
    K = st.number_input("Potassium (K)", min_value=0, max_value=200, value=50)
    
    # Weather selection
    use_live_weather = st.radio("Choose Weather Data:", ["Live Weather", "Custom Weather"], index=0)

    if use_live_weather == "Live Weather":
        temperature, humidity = get_weather()
        if temperature is None or humidity is None:
            st.warning("⚠️ Could not fetch live weather data. Using default values.")
            temperature, humidity = 25.0, 50.0
    else:
        temperature = st.number_input("Temperature (°C)", min_value=0.0, max_value=50.0, value=25.0)
        humidity = st.number_input("Humidity (%)", min_value=0.0, max_value=100.0, value=50.0)

    pH = st.number_input("pH Level", min_value=0.0, max_value=14.0, value=7.0)
    rainfall = st.number_input("Rainfall (mm)", min_value=0.0, max_value=500.0, value=100.0)

    # Predict Crop
    if st.button("Predict Crop"):
        # Ensure input matches the training feature names
        # Create DataFrame with correct column names
        feature_names = ["N", "P", "K", "temperature", "humidity", "pH", "rainfall"]
        input_data = pd.DataFrame([[N, P, K, temperature, humidity, pH, rainfall]], columns=feature_names)

# Predict using the correct format
        prediction = model.predict(input_data)[0]

        st.success(f"🌾 Recommended Crop: {prediction}")

        # Save Prediction to DB
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute(
            "INSERT INTO predictions (nitrogen, phosphorus, potassium, pH, rainfall, crop, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)", 
            (N, P, K, pH, rainfall, prediction, timestamp)
        )
        conn.commit()
        
    # Show Smart Farming Reminders
        reminders = get_farming_reminders(prediction)
        if reminders:
            for reminder in reminders:
                st.warning(reminder)

        
        # Save the predicted crop in session state for fertilizer advice
        st.session_state['predicted_crop'] = prediction

    # View Past Predictions
    if st.checkbox("📜 View Past Predictions"):
        df = pd.read_sql("SELECT * FROM predictions", conn)
        st.dataframe(df)

    # Download Predictions
    if st.button("📥 Download Predictions as CSV"):
        df = pd.read_sql("SELECT * FROM predictions", conn)
        csv_data = df.to_csv(index=False)
        st.download_button("Download CSV", data=csv_data, file_name="crop_predictions.csv", mime="text/csv")

with tabs[1]:
    st.title(" Fertilizer Advice")
    
    if 'predicted_crop' in st.session_state:
        crop_name = st.session_state['predicted_crop']
        st.write(f"Based on the predicted crop: **{crop_name}**")
    else:
        crop_name = st.text_input("Enter Crop Name for Fertilizer Advice", value="")

    if crop_name:
        fertilizer_advice = {
            "rice": "Urea, DAP, MOP",
            "maize": "Urea, DAP, MOP",
            "chickpea": "SSP, DAP",
            "kidneybeans": "DAP, SSP",
            "pigeonpeas": "SSP, Urea",
            "mothbeans": "DAP, SSP",
            "mungbean": "DAP, SSP",
            "blackgram": "SSP, DAP",
            "lentil": "SSP, DAP",
            "pomegranate": "NPK 17:17:17, MOP",
            "banana": "Urea, MOP, DAP",
            "mango": "NPK 10:26:26, Urea",
            "grapes": "DAP, MOP, NPK 19:19:19",
            "watermelon": "Urea, DAP, MOP",
            "muskmelon": "Urea, DAP, MOP",
            "apple": "NPK 12:12:12, Urea",
            "orange": "NPK 15:15:15, MOP",
            "papaya": "Urea, DAP, MOP",
            "coconut": "NPK 10:26:26, MOP",
            "cotton": "Urea, DAP, MOP",
            "jute": "Urea, SSP, MOP",
            "coffee": "NPK 15:15:15, MOP"
        }
        advice = fertilizer_advice.get(crop_name.lower(), "No specific fertilizer advice available for this crop. Please consult an agronomist.")
        st.info(f"Fertilizer Advice for {crop_name.capitalize()}: {advice}")
    else:
        st.write("Please enter or predict a crop to get fertilizer advice.")

    # Adding Crop Calendar
    st.subheader(" Crop Calendar")
    
    crop_calendar = {
        "rice": "🌱 Sow: June-July | 🌾 Harvest: Oct-Nov",
        "maize": "🌱 Sow: May-July | 🌾 Harvest: Sept-Nov",
        "chickpea": "🌱 Sow: Oct-Nov | 🌾 Harvest: Feb-Apr",
        "kidneybeans": "🌱 Sow: June-July | 🌾 Harvest: Sept-Oct",
        "pigeonpeas": "🌱 Sow: June-July | 🌾 Harvest: Dec-Jan",
        "mothbeans": "🌱 Sow: June-July | 🌾 Harvest: Sept-Oct",
        "mungbean": "🌱 Sow: July-Aug | 🌾 Harvest: Sept-Oct",
        "blackgram": "🌱 Sow: June-July | 🌾 Harvest: Sept-Oct",
        "lentil": "🌱 Sow: Oct-Nov | 🌾 Harvest: Feb-Apr",
        "pomegranate": "🌱 Planting: Feb-March | 🌾 Harvest: Aug-Nov",
        "banana": "🌱 Planting: Throughout the year | 🌾 Harvest: 12-15 months after planting",
        "mango": "🌱 Planting: June-Aug | 🌾 Harvest: April-July",
        "grapes": "🌱 Planting: Nov-Dec | 🌾 Harvest: March-May",
        "watermelon": "🌱 Sow: Jan-March | 🌾 Harvest: April-June",
        "muskmelon": "🌱 Sow: Feb-March | 🌾 Harvest: May-June",
        "apple": "🌱 Planting: Dec-Jan | 🌾 Harvest: Aug-Oct",
        "orange": "🌱 Planting: June-July | 🌾 Harvest: Nov-Jan",
        "papaya": "🌱 Planting: Feb-April | 🌾 Harvest: 8-10 months after planting",
        "coconut": "🌱 Planting: June-July | 🌾 Harvest: Throughout the year",
        "cotton": "🌱 Sow: April-May | 🌾 Harvest: Sept-Dec",
        "jute": "🌱 Sow: March-April | 🌾 Harvest: Aug-Sept",
        "coffee": "🌱 Planting: June-Aug | 🌾 Harvest: Dec-Feb",
    }

    # Display the calendar for the predicted or selected crop
    if crop_name.lower() in crop_calendar:
        st.info(f"📌 {crop_name.capitalize()} Calendar: {crop_calendar[crop_name.lower()]}")
    else:
        st.warning("Please select or predict a crop to view its calendar.")



with tabs[2]:
    st.title(" Weather Forecast (3 Days)")
    forecast = get_weather_forecast()

    if forecast:
        st.write(" 3-Day Weather Forecast for India:")
        forecast_data = []
        for day in forecast:
            date = day['date']
            avg_temp = day['day']['avgtemp_c']
            avg_humidity = day['day']['avghumidity']
            forecast_data.append([date, avg_temp, avg_humidity])

        forecast_df = pd.DataFrame(forecast_data, columns=["Date", "Avg Temp (°C)", "Avg Humidity (%)"])
        st.dataframe(forecast_df)

    else:
        st.write("⚠️ Could not fetch weather forecast data.")



# Close DB Connection
conn.close()
