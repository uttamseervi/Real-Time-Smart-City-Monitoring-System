import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Streamlit config
st.set_page_config(page_title="Smart City Dashboard", layout="wide")

st.title("🌆 Smart City Real-Time Monitoring Dashboard")

# --------- Dummy Live Data ---------
st.subheader("📊 Live Traffic & AQI Metrics")

# Creating dummy live data
live_data = pd.DataFrame({
    "Location": ["Downtown", "Uptown", "Suburbs", "Industrial Zone"],
    "Traffic Flow (vehicles/hr)": [320, 210, 180, 400],
    "Air Quality Index (AQI)": [85, 60, 55, 110],
    "Last Updated": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")] * 4
})

st.write(live_data)

# --------- Dummy Historical Data ---------
st.subheader("📈 Historical Trends")

# Creating dummy historical data
date_range = [datetime.now() - timedelta(days=i) for i in range(30)][::-1]
historical = pd.DataFrame({
    "Date": date_range,
    "Downtown AQI": np.random.randint(70, 120, size=30),
    "Uptown AQI": np.random.randint(50, 90, size=30),
    "Traffic Volume": np.random.randint(200, 500, size=30)
}).set_index("Date")

st.line_chart(historical)
