# Real-Time Smart City Monitoring System

## 🚀 Project Overview

This project is a Big Data Analytics solution designed to enable **real-time monitoring of smart cities** using streaming data from multiple sources. It focuses on integrating **traffic**, **air quality (AQI)**, and **weather** data to provide insights, alerts, and predictions that can help mitigate congestion and pollution issues in urban environments.

The system collects and processes live data using **Kafka**, **Spark Streaming**, and stores enriched outputs in **MongoDB**, which is then visualized on an interactive dashboard built with **Streamlit**.

---

## ❓ Why This Project?

- **Real-world relevance**: Traffic congestion and pollution are key challenges in modern urban life.
- **Scalable and Modular**: Built using big data tools that are scalable and production-grade.
- **Analytics + Visualization**: Combines live analytics, predictions, and easy-to-read dashboards.
- **Course Goal**: Demonstrates end-to-end Big Data processing using industry tools.

---

## 🧳 What the Project Aims to Do

- Monitor traffic, air quality, and weather **in real time**.
- Detect **pollution spikes** caused by traffic congestion.
- Suggest **alternate routes** based on congestion levels.
- Predict **future AQI trends** using historical data.
- Provide city planners with a dashboard to make **data-driven decisions**.

---

## 📊 System Architecture & Data Flow

```
 Kafka Topic (traffic)   Kafka Topic (aqi)   Kafka Topic (weather)
        ↓                        ↓                 ↓
         ------------ Spark Streaming ------------
                         ↓
           Cleaned + Enriched DataStream
                         ↓
          MongoDB (for dashboard + ML)
                         ↓
     Dashboard (Real-time AQI, Traffic, Routes)
```

---

## ⚖️ Tools Used and Their Roles

### 1. **Apache Kafka**
- Used for **real-time data ingestion**.
- Three topics: `traffic-data`, `aqi-data`, and `weather-data`.
- Simulated data producers push JSON data to these topics every second.

### 2. **Apache Spark Streaming**
- Consumes data from Kafka topics.
- Cleans and enriches the data.
- Joins datasets based on timestamps and locations.
- Calculates metrics like:
  - `congestion_level`
  - `pollution_risk`
  - `recommended_alternate_routes`
- Saves results to MongoDB.

### 3. **MongoDB**
- Acts as a **NoSQL storage layer**.
- Stores enriched, time-series data for dashboard queries.
- Optional: stores historical data for ML model training.

### 4. **Streamlit**
- Interactive dashboard to visualize:
  - Real-time traffic and AQI levels.
  - Map with congestion and pollution zones.
  - Time-series trends.
  - Predicted AQI for upcoming hours/days.

---

## 📈 Dashboard Insights

The dashboard displays:

- ✅ **Live Junction Status**: Traffic density, average speed, AQI, pollution risk.
- 🌍 **Map View**: City map with markers indicating congestion and AQI level.
- ⏲️ **Historical Trends**: Time series graphs for AQI and traffic.
- ⚖️ **Predicted AQI**: Future AQI levels using ML models.
- ➡️ **Suggested Routes**: Alternate junctions when congestion is high.

---

## 🔹 Datasets & Sources

| Type     | Source or Simulation        | Notes |
|----------|-----------------------------|-------|
| Traffic  | Simulated (Python script)   | Vehicles per minute, speed, junction |
| AQI      | Simulated or from API (e.g., OpenAQ) | PM2.5, PM10, NO2, CO levels |
| Weather  | OpenWeatherMap API or simulated | Temperature, humidity, wind speed |

### Sample APIs:
- OpenAQ API: [https://docs.openaq.org/](https://docs.openaq.org/)
- OpenWeatherMap API: [https://openweathermap.org/api](https://openweathermap.org/api)

---

## 🚧 Project Setup (High-Level)

### 1. Create and activate a virtual environment
```
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

### 2. Start Kafka & MongoDB (via Docker Compose)
```
docker-compose up -d  # in kafka-setup/ and mongodb-setup/
```

### 3. Run the simulators to generate live data
```
python traffic_producer.py
python aqi_producer.py
python weather_producer.py
```

### 4. Run Spark Streaming job
```
spark-submit main_stream.py
```

### 5. Run Dashboard app
```
python app.py  # Dash frontend
```

---

## 🔄 Optional: ML for AQI Prediction
- Historical data used to train a model to predict AQI levels.
- Model trained using scikit-learn.
- Predictions visualized on the dashboard.

---

## 🌐 Future Enhancements
- Use real data from sensors or city APIs.
- Incorporate alerts (SMS/email) for extreme pollution levels.
- Use machine learning for traffic prediction.
- Enable route optimization using real map APIs.

---

## 📊 Conclusion
This project shows how Big Data tools can be integrated to solve **real-world urban challenges** like traffic and pollution in real-time. With live dashboards, intelligent insights, and predictive analytics, this system can help city planners and residents make informed decisions for a cleaner, smarter city.


## 🏆 Tech Stack
- Python, Kafka, Spark, MongoDB, Dash, Docker

