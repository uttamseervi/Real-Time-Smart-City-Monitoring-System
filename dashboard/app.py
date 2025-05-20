import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import threading
from datetime import datetime
import numpy as np  # Add numpy for radar chart calculations

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
    fig1.update_traces(hovertemplate="Time: %{x}<br>Speed: %{y:.1f} km/h<br>Type: %{fullData.name}")
    st.plotly_chart(fig1, use_container_width=True)

with col_b:
    latest = traffic_df.iloc[-1]
    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=latest["currentSpeed"],
        title={'text': "Current Speed (km/h)"},
        gauge={
            'axis': {'range': [0, latest["freeFlowSpeed"] * 1.5]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, latest["freeFlowSpeed"] * 0.5], 'color': "red"},
                {'range': [latest["freeFlowSpeed"] * 0.5, latest["freeFlowSpeed"]], 'color': "yellow"},
                {'range': [latest["freeFlowSpeed"], latest["freeFlowSpeed"] * 1.5], 'color': "green"}
            ]
        },
        number={'suffix': " km/h"}
    ))
    gauge.update_layout(
        annotations=[{
            'text': f"Free Flow: {latest['freeFlowSpeed']:.1f} km/h",
            'showarrow': False,
            'x': 0.5,
            'y': -0.1
        }]
    )
    st.plotly_chart(gauge, use_container_width=True)

# Add Traffic Radar Chart
st.subheader("📊 Traffic Metrics Radar")
traffic_metrics = {
    'Speed Ratio': (latest["currentSpeed"] / latest["freeFlowSpeed"]) * 100,
    'Travel Time Ratio': (latest["currentTravelTime"] / latest["freeFlowTravelTime"]) * 100,
    'Congestion Level': (1 - (latest["currentSpeed"] / latest["freeFlowSpeed"])) * 100,
    'Flow Efficiency': (latest["currentSpeed"] / latest["freeFlowSpeed"]) * 100,
    'Traffic Health': (1 - (latest["currentTravelTime"] / latest["freeFlowTravelTime"])) * 100
}

# Create tooltips for traffic metrics
traffic_tooltips = {
    'Speed Ratio': 'Percentage of current speed compared to free flow speed',
    'Travel Time Ratio': 'Percentage of current travel time compared to free flow time',
    'Congestion Level': 'Level of congestion (100% = maximum congestion)',
    'Flow Efficiency': 'How efficiently traffic is flowing compared to ideal conditions',
    'Traffic Health': 'Overall health of traffic flow (100% = optimal conditions)'
}

fig_traffic_radar = go.Figure()
fig_traffic_radar.add_trace(go.Scatterpolar(
    r=[v for v in traffic_metrics.values()],
    theta=[k for k in traffic_metrics.keys()],
    fill='toself',
    name='Current Traffic',
    hovertemplate="%{theta}: %{r:.1f}%<br>%{customdata}",
    customdata=[traffic_tooltips[k] for k in traffic_metrics.keys()]
))

fig_traffic_radar.update_layout(
    polar=dict(
        radialaxis=dict(
            visible=True,
            range=[0, 100]
        )),
    showlegend=False,
    title="Traffic Performance Metrics"
)
st.plotly_chart(fig_traffic_radar, use_container_width=True)

st.markdown("---")

# ── WEATHER SECTION ────────────────────────────────────────────────────────────
st.header("🌦️ Weather Monitoring")
col_c, col_d = st.columns(2)
with col_c:
    fig2 = px.line(weather_df, x="event_time", y=["temp_C", "humidity"],
                   labels={"value": "Value"},
                   title=f"Last {records} Points: Temp & Humidity")
    fig2.update_traces(hovertemplate="Time: %{x}<br>Value: %{y:.1f}<br>Type: %{fullData.name}")
    st.plotly_chart(fig2, use_container_width=True)

with col_d:
    current = weather_df.iloc[-1]
    st.subheader("Current Conditions")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("🌡️ Temp", f"{current['temp_C']:.1f} °C", 
                 help="Current temperature in Celsius")
        st.metric("💧 Humidity", f"{current['humidity']}%",
                 help="Relative humidity percentage in the air")
        st.metric("📈 Pressure", f"{current['pressure']} hPa",
                 help="Atmospheric pressure in hectopascals")
    with c2:
        st.metric("💨 Wind", f"{current['wind_speed']} m/s",
                 help="Current wind speed in meters per second")
        st.metric("☁ Weather", current['weather'],
                 help="Current weather conditions")
    st.write(f"📝 {current['description']}")

# Add Weather Radar Chart
st.subheader("📊 Weather Conditions Radar")
# Normalize weather metrics to 0-100 scale
temp_normalized = ((current['temp_C'] + 20) / 50) * 100  # Assuming -20°C to 30°C range
humidity_normalized = current['humidity']  # Already in 0-100
pressure_normalized = ((current['pressure'] - 900) / 200) * 100  # Assuming 900-1100 hPa range
wind_normalized = (current['wind_speed'] / 20) * 100  # Assuming 0-20 m/s range

weather_metrics = {
    'Temperature': temp_normalized,
    'Humidity': humidity_normalized,
    'Pressure': pressure_normalized,
    'Wind Speed': wind_normalized,
    'Weather Impact': 100 if 'rain' in current['description'].lower() else 50
}

# Create tooltips for weather metrics
weather_tooltips = {
    'Temperature': f'Normalized temperature ({current["temp_C"]:.1f}°C)',
    'Humidity': f'Relative humidity ({current["humidity"]}%)',
    'Pressure': f'Atmospheric pressure ({current["pressure"]} hPa)',
    'Wind Speed': f'Wind speed ({current["wind_speed"]} m/s)',
    'Weather Impact': 'Impact of current weather conditions on city operations'
}

fig_weather_radar = go.Figure()
fig_weather_radar.add_trace(go.Scatterpolar(
    r=[v for v in weather_metrics.values()],
    theta=[k for k in weather_metrics.keys()],
    fill='toself',
    name='Current Weather',
    hovertemplate="%{theta}: %{r:.1f}%<br>%{customdata}",
    customdata=[weather_tooltips[k] for k in weather_metrics.keys()]
))

fig_weather_radar.update_layout(
    polar=dict(
        radialaxis=dict(
            visible=True,
            range=[0, 100]
        )),
    showlegend=False,
    title="Weather Conditions Overview"
)
st.plotly_chart(fig_weather_radar, use_container_width=True)

st.markdown("---")

# ── TRAVEL TIME HISTORY ────────────────────────────────────────────────────────
st.subheader("⏱️ Travel Time Comparison")
fig3 = px.bar(traffic_df.tail(20), x="event_time", y=["currentTravelTime", "freeFlowTravelTime"],
              barmode="group", title="Recent Travel Time vs Free Flow Time")
fig3.update_traces(hovertemplate="Time: %{x}<br>Travel Time: %{y:.1f} minutes<br>Type: %{fullData.name}")
st.plotly_chart(fig3, use_container_width=True)

# ── REAL-TIME SPEED FLUCTUATION ────────────────────────────────────────────────
st.header("📉 Real-Time Speed Fluctuation")

# Initialize session state for historical data if not exists
if 'hist_data' not in st.session_state:
    st.session_state.hist_data = {
        'times': [],
        'speeds': [],
        'free_flow_speeds': []
    }

# Get the latest data point
latest_time = traffic_df.iloc[-1]['event_time']
latest_speed = traffic_df.iloc[-1]['currentSpeed']
latest_free_flow = traffic_df.iloc[-1]['freeFlowSpeed']

# Update historical data if we have new data
if 'last_update_time' not in st.session_state or latest_time > st.session_state.last_update_time:
    st.session_state.hist_data['times'].append(latest_time)
    st.session_state.hist_data['speeds'].append(latest_speed)
    st.session_state.hist_data['free_flow_speeds'].append(latest_free_flow)
    st.session_state.last_update_time = latest_time

# Trim the historical data to the desired length
max_points = hist_len
st.session_state.hist_data['times'] = st.session_state.hist_data['times'][-max_points:]
st.session_state.hist_data['speeds'] = st.session_state.hist_data['speeds'][-max_points:]
st.session_state.hist_data['free_flow_speeds'] = st.session_state.hist_data['free_flow_speeds'][-max_points:]

# Create the fluctuation chart
fluct_df = pd.DataFrame({
    'time': st.session_state.hist_data['times'],
    'Current Speed': st.session_state.hist_data['speeds'],
    'Free Flow Speed': st.session_state.hist_data['free_flow_speeds']
})

# Calculate some statistics
if len(st.session_state.hist_data['speeds']) > 1:
    speed_changes = np.diff(st.session_state.hist_data['speeds'])
    avg_change = np.mean(np.abs(speed_changes))
    max_change = np.max(np.abs(speed_changes))
    
    # Display statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Average Speed Change", f"{avg_change:.1f} km/h")
    with col2:
        st.metric("Max Speed Change", f"{max_change:.1f} km/h")
    with col3:
        st.metric("Current Speed", f"{latest_speed:.1f} km/h")

# Create the fluctuation chart
fig4 = go.Figure()
fig4.add_trace(go.Scatter(
    x=fluct_df['time'],
    y=fluct_df['Current Speed'],
    name='Current Speed',
    line=dict(color='blue', width=2),
    hovertemplate="Time: %{x}<br>Speed: %{y:.1f} km/h"
))
fig4.add_trace(go.Scatter(
    x=fluct_df['time'],
    y=fluct_df['Free Flow Speed'],
    name='Free Flow Speed',
    line=dict(color='green', width=2, dash='dash'),
    hovertemplate="Time: %{x}<br>Free Flow Speed: %{y:.1f} km/h"
))

fig4.update_layout(
    title=f'Speed Fluctuations (Last {len(fluct_df)} Updates)',
    xaxis_title='Time',
    yaxis_title='Speed (km/h)',
    hovermode='x unified',
    showlegend=True,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)

# Add a horizontal line for the current speed
fig4.add_shape(
    type="line",
    x0=fluct_df['time'].min(),
    y0=latest_speed,
    x1=fluct_df['time'].max(),
    y1=latest_speed,
    line=dict(color="red", width=2, dash="dot"),
)

st.plotly_chart(fig4, use_container_width=True)

# Add speed change analysis
if len(st.session_state.hist_data['speeds']) > 1:
    st.subheader("📊 Speed Change Analysis")
    
    # Calculate speed change percentages
    speed_changes_pct = (np.diff(st.session_state.hist_data['speeds']) / st.session_state.hist_data['speeds'][:-1]) * 100
    
    # Create a histogram of speed changes
    fig5 = go.Figure()
    fig5.add_trace(go.Histogram(
        x=speed_changes_pct,
        nbinsx=20,
        name='Speed Changes',
        marker_color='blue',
        opacity=0.7
    ))
    
    fig5.update_layout(
        title='Distribution of Speed Changes (%)',
        xaxis_title='Speed Change (%)',
        yaxis_title='Frequency',
        showlegend=False
    )
    
    st.plotly_chart(fig5, use_container_width=True)

# ── INSIGHTS & ALERTS ──────────────────────────────────────────────────────────
st.header("🧠 Insights & Alerts")

# Traffic Alerts
traffic_alerts = []
latest = traffic_df.iloc[-1]
speed_ratio = latest['currentSpeed'] / latest['freeFlowSpeed']
travel_time_ratio = latest['currentTravelTime'] / latest['freeFlowTravelTime']

# Debug information
st.write("### Debug Information")
st.write(f"Current Speed: {latest['currentSpeed']:.1f} km/h")
st.write(f"Free Flow Speed: {latest['freeFlowSpeed']:.1f} km/h")
st.write(f"Speed Ratio: {speed_ratio:.2%}")
st.write(f"Travel Time Ratio: {travel_time_ratio:.2%}")

# Speed-based alerts with more granular thresholds
if speed_ratio < 0.3:
    traffic_alerts.append(f"🚨 Critical Traffic: Speed below 30% of free flow (Current: {latest['currentSpeed']:.1f} km/h)")
elif speed_ratio < 0.5:
    traffic_alerts.append(f"⚠️ Heavy Traffic: Speed below 50% of free flow (Current: {latest['currentSpeed']:.1f} km/h)")
elif speed_ratio < 0.7:
    traffic_alerts.append(f"⚠️ Moderate Traffic: Speed below 70% of free flow (Current: {latest['currentSpeed']:.1f} km/h)")
elif speed_ratio > 1.1:
    traffic_alerts.append(f"✅ Excellent Flow: Speed above free flow (Current: {latest['currentSpeed']:.1f} km/h)")

# Travel time alerts with more context
if travel_time_ratio > 2.0:
    traffic_alerts.append(f"⏰ Severe Delay: Travel time {travel_time_ratio:.1f}x free flow time")
elif travel_time_ratio > 1.5:
    traffic_alerts.append(f"⏰ Moderate Delay: Travel time {travel_time_ratio:.1f}x free flow time")
elif travel_time_ratio < 1.1:
    traffic_alerts.append(f"✅ Good Flow: Travel time near free flow conditions")

# Speed fluctuation alerts with more detail
if len(st.session_state.hist_data['speeds']) > 1:
    recent_speeds = st.session_state.hist_data['speeds'][-5:]  # Last 5 speed readings
    speed_std = np.std(recent_speeds)
    speed_mean = np.mean(recent_speeds)
    
    if speed_std > speed_mean * 0.3:  # High variability
        traffic_alerts.append(f"🔄 Unstable Traffic: High speed variability ({speed_std:.1f} km/h std dev)")
    
    # Sudden speed change alert
    last_speed_change = abs(recent_speeds[-1] - recent_speeds[-2])
    if last_speed_change > speed_mean * 0.2:  # More than 20% change
        traffic_alerts.append(f"⚡ Sudden Speed Change: {last_speed_change:.1f} km/h change detected")

# Always show at least one traffic status
if not traffic_alerts:
    if speed_ratio >= 0.7:
        traffic_alerts.append(f"✅ Normal Traffic Flow: Speed at {speed_ratio:.1%} of free flow")
    else:
        traffic_alerts.append(f"ℹ️ Traffic Status: Current speed {latest['currentSpeed']:.1f} km/h")

# Weather Alerts
weather_alerts = []
current = weather_df.iloc[-1]

# Temperature alerts
if current['temp_C'] > 35:
    weather_alerts.append("🌡️ Heat Alert: Temperature above 35°C")
elif current['temp_C'] > 30:
    weather_alerts.append("🌡️ High Temperature: Above 30°C")
elif current['temp_C'] < 5:
    weather_alerts.append("❄️ Cold Alert: Temperature below 5°C")

# Humidity alerts
if current['humidity'] > 90:
    weather_alerts.append("💧 Very High Humidity: Above 90%")
elif current['humidity'] > 80:
    weather_alerts.append("💧 High Humidity: Above 80%")
elif current['humidity'] < 30:
    weather_alerts.append("🏜️ Low Humidity: Below 30%")

# Pressure alerts
if current['pressure'] < 980:
    weather_alerts.append("🌪️ Low Pressure: Potential storm conditions")
elif current['pressure'] > 1020:
    weather_alerts.append("☀️ High Pressure: Stable weather conditions")

# Wind alerts
if current['wind_speed'] > 15:
    weather_alerts.append("💨 Strong Winds: Above 15 m/s")
elif current['wind_speed'] > 10:
    weather_alerts.append("💨 Moderate Winds: Above 10 m/s")

# Weather condition specific alerts
weather_desc = current['description'].lower()
if 'rain' in weather_desc:
    if current['humidity'] > 85:
        weather_alerts.append("☔ Heavy Rain Risk: High humidity with rain")
    else:
        weather_alerts.append("🌧️ Rain Conditions: Drive carefully")
if 'fog' in weather_desc:
    weather_alerts.append("🌫️ Fog Alert: Reduced visibility")
if 'storm' in weather_desc:
    weather_alerts.append("⛈️ Storm Warning: Severe weather conditions")

# Combined Alerts Display
st.subheader("🚨 Active Alerts")

# Calculate health score with more granular factors
cscore = 0
if speed_ratio < 0.3: cscore += 2
elif speed_ratio < 0.5: cscore += 1
if travel_time_ratio > 2.0: cscore += 2
elif travel_time_ratio > 1.5: cscore += 1
if current['humidity'] > 90: cscore += 1
if current['temp_C'] > 35 or current['temp_C'] < 5: cscore += 1
if current['wind_speed'] > 15: cscore += 1
if 'storm' in weather_desc: cscore += 2

health = max(0, 100 - (cscore * 10))  # Each factor reduces score by 10 points

# Display health score with appropriate styling
health_status = "Good" if health > 70 else "Moderate" if health > 40 else "Poor"
health_delta = f"{health_status} ({health}/100)"
st.metric(
    "🩺 City Health Score",
    f"{health}/100",
    delta=health_delta,
    delta_color="normal"
)

# Display alerts in columns
if traffic_alerts or weather_alerts:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚦 Traffic Alerts")
        for alert in traffic_alerts:
            st.warning(alert)
    
    with col2:
        st.subheader("🌦️ Weather Alerts")
        for alert in weather_alerts:
            st.warning(alert)
else:
    st.success("✅ All systems operating normally!")

# Add a summary of conditions
st.subheader("📊 Current Conditions Summary")
summary_col1, summary_col2 = st.columns(2)

with summary_col1:
    st.write("**Traffic Status:**")
    st.write(f"- Current Speed: {latest['currentSpeed']:.1f} km/h")
    st.write(f"- Free Flow Speed: {latest['freeFlowSpeed']:.1f} km/h")
    st.write(f"- Speed Ratio: {speed_ratio:.1%}")
    st.write(f"- Travel Time Ratio: {travel_time_ratio:.1%}")

with summary_col2:
    st.write("**Weather Status:**")
    st.write(f"- Temperature: {current['temp_C']:.1f}°C")
    st.write(f"- Humidity: {current['humidity']}%")
    st.write(f"- Wind Speed: {current['wind_speed']} m/s")
    st.write(f"- Pressure: {current['pressure']} hPa")

# ── RAW DATA (OPTIONAL) ────────────────────────────────────────────────────────
with st.expander("📄 View Raw Data"):
    st.subheader("Traffic Data")
    st.caption("Raw traffic data showing all metrics over time")
    st.dataframe(traffic_df)
    st.subheader("Weather Data")
    st.caption("Raw weather data showing all environmental conditions over time")
    st.dataframe(weather_df)
