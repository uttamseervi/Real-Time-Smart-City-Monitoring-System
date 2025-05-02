import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import threading
from datetime import datetime, timezone

# ── PAGE CONFIG (must be first Streamlit call) ─────────────────────────────────
st.set_page_config(page_title="Smart City Dashboard", layout="wide")

# ── REAL-TIME WATCHER ───────────────────────────────────────────────────────────
# Launch MongoDB change stream listeners before other st calls
MONGO_URI = (
    "mongodb+srv://uttamseervi:uttamseervi0045*@smartcitycluster."
    "atuzu9o.mongodb.net/?retryWrites=true&w=majority&appName=SmartCityCluster"
)
DB_NAME     = "smartcity"
TRAFFIC_COL = "traffic_data"
WEATHER_COL = "weather_data"

client = MongoClient(MONGO_URI)
db     = client[DB_NAME]
tcol   = db[TRAFFIC_COL]
wcol   = db[WEATHER_COL]


def start_watchers():
    def watch_collection(col):
        try:
            with col.watch([{'$match':{'operationType':'insert'}}], full_document='updateLookup') as stream:
                for _ in stream:
                    st.experimental_rerun()
        except Exception:
            pass
    threading.Thread(target=watch_collection, args=(tcol,), daemon=True).start()
    threading.Thread(target=watch_collection, args=(wcol,), daemon=True).start()

if 'watchers_started' not in st.session_state:
    start_watchers()
    st.session_state['watchers_started'] = True

# ── SIDEBAR CONTROLS ────────────────────────────────────────────────────────────
st.sidebar.header("Settings")
default_limit = 100
records = st.sidebar.slider("Records to fetch:", 10, 500, default_limit, 10)
hist_len = st.sidebar.slider("History length:", 20, 200, 50, 10)

# ── DATA LOADING ────────────────────────────────────────────────────────────────
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

# ── APP TITLE ────────────────────────────────────────────────────────────────────
st.title("🌆 Smart City Monitoring (Real-Time)")

# ── LOAD DATA ───────────────────────────────────────────────────────────────────
traffic_df = load_traffic(records)
weather_df = load_weather(records)
if traffic_df.empty or weather_df.empty:
    st.warning("Awaiting data… ensure producers & consumers are running.")
    st.stop()

# ── HEADER: Location & Last Update ──────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    st.subheader("📍 Location")
    st.write(weather_df.iloc[-1]["location"])
with col2:
    st.subheader("🕒 Last Update")
    last_t = max(traffic_df["event_time"].max(), weather_df["event_time"].max())
    st.write(last_t.strftime("%Y-%m-%d %H:%M:%S UTC"))
st.markdown("---")

# ── TRAFFIC SECTION ─────────────────────────────────────────────────────────────
st.header("🚦 Traffic Monitoring")
col_a, col_b, col_c = st.columns([2,2,1])
with col_a:
    fig1 = px.line(traffic_df, x="event_time", y=["currentSpeed","freeFlowSpeed"],
                   labels={"value":"Speed (km/h)"}, title=f"Last {records} Points: Speeds")
    st.plotly_chart(fig1, use_container_width=True)
with col_b:
    cnts = traffic_df["congestion_level"].value_counts()
    fig2 = px.pie(names=cnts.index, values=cnts.values, title="Congestion Distribution")
    st.plotly_chart(fig2, use_container_width=True)
with col_c:
    if traffic_df["roadClosure"].any(): st.error("⚠️ Road Closure Reported!")
    latest_traffic = traffic_df.iloc[-1]
    st.metric("Latest Speed", f"{latest_traffic['currentSpeed']} km/h")
st.markdown("---")

# ── WEATHER SECTION ─────────────────────────────────────────────────────────────
st.header("🌦️ Weather Monitoring")
col_d, col_e = st.columns(2)
with col_d:
    fig3 = px.line(weather_df, x="event_time", y=["temp_C","humidity"],
                   labels={"value":"Value"}, title=f"Last {records} Points: Temp & Humidity")
    st.plotly_chart(fig3, use_container_width=True)
with col_e:
    weather_curr = weather_df.iloc[-1]
    st.subheader("Current Conditions")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("🌡️ Temp", f"{weather_curr['temp_C']:.1f} °C")
        st.metric("💧 Humidity", f"{weather_curr['humidity']}%")
        st.metric("📈 Pressure", f"{weather_curr['pressure']} hPa")
    with c2:
        st.metric("💨 Wind", f"{weather_curr['wind_speed']} m/s")
        st.metric("☁ Condition", weather_curr['weather'])
    st.write(f"📝 {weather_curr['description']}")
st.markdown("---")

# ── REAL-TIME FLUCTUATION ───────────────────────────────────────────────────────
st.header("📈 Real-Time Speed Fluctuation")
if 'hist_times' not in st.session_state:
    st.session_state.hist_times = []
    st.session_state.hist_speed = []
# Append new only if timestamp advanced
latest_time = traffic_df.iloc[-1]['event_time']
if 'last_time' not in st.session_state or latest_time > st.session_state['last_time']:
    st.session_state.hist_times.append(latest_time)
    st.session_state.hist_speed.append(traffic_df.iloc[-1]['currentSpeed'])
    st.session_state['last_time'] = latest_time
# Trim history
tail = min(len(st.session_state.hist_times), hist_len)
st.session_state.hist_times = st.session_state.hist_times[-tail:]
st.session_state.hist_speed = st.session_state.hist_speed[-tail:]
# Plot
fluct_df = pd.DataFrame({'time': st.session_state.hist_times, 'speed': st.session_state.hist_speed})
fig4 = px.line(fluct_df, x='time', y='speed', labels={'speed':'Speed (km/h)'}, title=f'Last {tail} Updates')
st.plotly_chart(fig4, use_container_width=True)

# ── INSIGHTS & ALERTS ──────────────────────────────────────────────────────────
st.header("🧠 Insights & Alerts")
alerts = []
if weather_curr['humidity']>80 and 'rain' in weather_curr['description'].lower():
    alerts.append("☔ High humidity + rain: waterlogging risk")
if latest_traffic['currentSpeed'] < 0.5 * latest_traffic['freeFlowSpeed']:
    alerts.append("🚨 Heavy congestion")
cscore = {'low':0,'medium':1,'high':2,'severe':3}.get(latest_traffic['congestion_level'],0)
wscore = 1 if weather_curr['humidity']>80 else 0
health = max(0,100-(cscore+wscore)*20)
st.metric("🩺 City Health Score", f"{health}/100")
if alerts:
    for a in alerts:
        st.warning(a)
else:
    st.success("✅ All clear!")
