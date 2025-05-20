import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import threading
from datetime import datetime

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Smart City Dashboard", layout="wide")

# ── MONGODB CONNECTION ─────────────────────────────────────────────────────────
MONGO_URI = "mongodb+srv://uttamseervi:uttamseervi0045*@smartcitycluster.atuzu9o.mongodb.net/?retryWrites=true&w=majority&appName=SmartCityCluster"
DB_NAME = "smartcity"
TRAFFIC_COL = "traffic_data"
WEATHER_COL = "weather_data"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
tcol = db[TRAFFIC_COL]
wcol = db[WEATHER_COL]

# ── REAL-TIME WATCHERS ─────────────────────────────────────────────────────────
def start_watchers():
    def watch_collection(col):
        try:
            with col.watch([{'$match': {'operationType': 'insert'}}], full_document='updateLookup') as stream:
                for _ in stream:
                    st.experimental_rerun()
        except Exception:
            pass
    threading.Thread(target=watch_collection, args=(tcol,), daemon=True).start()
    threading.Thread(target=watch_collection, args=(wcol,), daemon=True).start()

if 'watchers_started' not in st.session_state:
    start_watchers()
    st.session_state['watchers_started'] = True

# ── SIDEBAR CONTROLS ───────────────────────────────────────────────────────────
st.sidebar.header("Settings")
records = st.sidebar.slider("Records to fetch:", 10, 500, 100, 10)
hist_len = st.sidebar.slider("History length:", 20, 200, 50, 10)

# ── DATA LOADERS ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=5)
def load_traffic(n):
    df = pd.DataFrame(list(tcol.find().sort("timestamp", -1).limit(n)))
    if df.empty:
        return df
    df["event_time"] = pd.to_datetime(df["timestamp"], utc=True)
    return df.sort_values("event_time")

@st.cache_data(ttl=5)
def load_weather(n):
    df = pd.DataFrame(list(wcol.find().sort("timestamp", -1).limit(n)))
    if df.empty:
        return df
    df["event_time"] = pd.to_datetime(df["timestamp"], utc=True)
    df["temp_C"] = df["temperature"] - 273.15
    return df.sort_values("event_time")

# ── TITLE ──────────────────────────────────────────────────────────────────────
st.title("🌆 Smart City Monitoring (Real-Time)")

# ── DATA LOAD ──────────────────────────────────────────────────────────────────
traffic_df = load_traffic(records)
weather_df = load_weather(records)

if traffic_df.empty or weather_df.empty:
    st.warning("Awaiting data… ensure producers & consumers are running.")
    st.stop()

# ── LOCATION & LAST UPDATE ─────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    st.subheader("📍 Location")
    st.write(weather_df.iloc[-1]["location"])
with col2:
    st.subheader("🕒 Last Update")
    last_t = max(traffic_df["event_time"].max(), weather_df["event_time"].max())
    st.write(last_t.strftime("%Y-%m-%d %H:%M:%S UTC"))
st.markdown("---")

# ── TRAFFIC SECTION ────────────────────────────────────────────────────────────
st.header("🚦 Traffic Monitoring")
col_a, col_b = st.columns([2, 2])
with col_a:
    fig1 = px.line(traffic_df, x="event_time", y=["currentSpeed", "freeFlowSpeed"],
                   labels={"value": "Speed (km/h)"},
                   title=f"Last {records} Points: Speeds")
    st.plotly_chart(fig1, use_container_width=True)

with col_b:
    latest = traffic_df.iloc[-1]
    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=latest["currentSpeed"],
        title={'text': "Current Speed (km/h)"},
        gauge={'axis': {'range': [0, latest["freeFlowSpeed"] * 1.5]}}
    ))
    st.plotly_chart(gauge, use_container_width=True)

st.markdown("---")

# ── WEATHER SECTION ────────────────────────────────────────────────────────────
st.header("🌦️ Weather Monitoring")
col_c, col_d = st.columns(2)
with col_c:
    fig2 = px.line(weather_df, x="event_time", y=["temp_C", "humidity"],
                   labels={"value": "Value"},
                   title=f"Last {records} Points: Temp & Humidity")
    st.plotly_chart(fig2, use_container_width=True)

with col_d:
    current = weather_df.iloc[-1]
    st.subheader("Current Conditions")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("🌡️ Temp", f"{current['temp_C']:.1f} °C")
        st.metric("💧 Humidity", f"{current['humidity']}%")
        st.metric("📈 Pressure", f"{current['pressure']} hPa")
    with c2:
        st.metric("💨 Wind", f"{current['wind_speed']} m/s")
        st.metric("☁ Weather", current['weather'])
    st.write(f"📝 {current['description']}")

st.markdown("---")

# ── TRAVEL TIME HISTORY ────────────────────────────────────────────────────────
st.subheader("⏱️ Travel Time Comparison")
fig3 = px.bar(traffic_df.tail(20), x="event_time", y=["currentTravelTime", "freeFlowTravelTime"],
              barmode="group", title="Recent Travel Time vs Free Flow Time")
st.plotly_chart(fig3, use_container_width=True)

# ── REAL-TIME SPEED FLUCTUATION ────────────────────────────────────────────────
st.header("📉 Real-Time Speed Fluctuation")
if 'hist_times' not in st.session_state:
    st.session_state.hist_times = []
    st.session_state.hist_speed = []

latest_time = traffic_df.iloc[-1]['event_time']
if 'last_time' not in st.session_state or latest_time > st.session_state['last_time']:
    st.session_state.hist_times.append(latest_time)
    st.session_state.hist_speed.append(float(traffic_df.iloc[-1]['currentSpeed']))
    st.session_state['last_time'] = latest_time

tail = min(len(st.session_state.hist_times), hist_len)
st.session_state.hist_times = st.session_state.hist_times[-tail:]
st.session_state.hist_speed = st.session_state.hist_speed[-tail:]

fluct_df = pd.DataFrame({'time': st.session_state.hist_times, 'speed': st.session_state.hist_speed})
fig4 = px.line(fluct_df, x='time', y='speed', labels={'speed': 'Speed (km/h)'}, title=f'Last {tail} Updates')
st.plotly_chart(fig4, use_container_width=True)

# ── RAIN PREDICTION ────────────────────────────────────────────────────────────
st.header("🌧️ Rain Likelihood Estimation")
rain_likelihood = 0
if current['humidity'] > 80 and current['temp_C'] < 25 and current['wind_speed'] < 5:
    rain_likelihood = 80
elif current['humidity'] > 70:
    rain_likelihood = 60
elif current['humidity'] > 60:
    rain_likelihood = 40
else:
    rain_likelihood = 20

st.metric("🌧️ Rain Chance", f"{rain_likelihood}%")

radar_data = pd.DataFrame({
    "Metric": ["Humidity", "Wind Speed", "Pressure", "Temperature", "Feels Like"],
    "Value": [current['humidity'], current['wind_speed']*10, current['pressure']/10, current['temp_C'], current['feels_like']-273.15]
})
fig_radar = px.line_polar(radar_data, r="Value", theta="Metric", line_close=True, title="Environmental Overview", markers=True)
fig_radar.update_traces(fill='toself')
st.plotly_chart(fig_radar, use_container_width=True)




# ── INSIGHTS & ALERTS ──────────────────────────────────────────────────────────
st.header("🧠 Insights & Alerts")
alerts = []
if current['humidity'] > 80 and 'rain' in current['description'].lower():
    alerts.append("☔ High humidity + rain: waterlogging risk")
if latest['currentSpeed'] < 0.5 * latest['freeFlowSpeed']:
    alerts.append("🚨 Heavy traffic (speed below 50% of free flow)")

cscore = 1 if latest['currentSpeed'] < 0.5 * latest['freeFlowSpeed'] else 0
wscore = 1 if current['humidity'] > 80 else 0
health = max(0, 100 - (cscore + wscore) * 20)
st.metric("🩺 City Health Score", f"{health}/100")

if alerts:
    for a in alerts:
        st.warning(a)
else:
    st.success("✅ All clear!")

# ── RAW DATA (OPTIONAL) ────────────────────────────────────────────────────────
with st.expander("📄 View Raw Data"):
    st.subheader("Traffic Data")
    st.dataframe(traffic_df)
    st.subheader("Weather Data")
    st.dataframe(weather_df)
