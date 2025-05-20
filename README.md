# 🌆 Real-Time Smart City Monitoring System

## 🚀 Project Overview

This project presents a **Big Data Analytics platform** for **real-time monitoring of smart cities**. It aggregates and processes live data from multiple sources, including **traffic**, **air quality (AQI)**, and **weather**, to offer actionable insights, predictions, and alerts. It leverages industry-standard tools to build a scalable, real-time pipeline that informs city planners and residents, helping to mitigate congestion and pollution.

---

## ❓ Why This Project?

- 🛣️ **Urban Relevance**: Tackles key modern challenges like traffic congestion and pollution.
- 🏗️ **Scalable & Modular**: Built on top of scalable Big Data technologies.
- 📈 **Actionable Insights**: Combines real-time analytics with intuitive visualizations.
- 🎓 **Academic Objective**: Demonstrates an end-to-end, production-ready data streaming pipeline.

---

## 🎯 Project Goals

- Live monitoring of traffic, AQI, and weather conditions.
- Detect **pollution spikes** linked with traffic congestion.
- Recommend **alternative routes** dynamically.
- Predict **AQI trends** using historical data and ML.
- Provide a **decision-making dashboard** for urban authorities.

---

## 🧱 System Architecture & Data Flow

```mermaid
graph TD
    A[Kafka Topics] --> B[Spark Streaming Engine]
    B --> C[Data Cleaning & Enrichment]
    C --> D[MongoDB Storage]
    D --> E[Streamlit Dashboard]
    A1[Traffic Data] --> A
    A2[AQI Data] --> A
    A3[Weather Data] --> A
    D --> F[ML Model Training (Optional)]
    F --> E
```

---

## ⚙️ Tools & Technologies

### 🔁 Apache Kafka
- Acts as the real-time **data ingestion layer**.
- Topics: `traffic-data`, `aqi-data`, `weather-data`.
- Simulated or API-based producers push JSON payloads every second.

### 🔄 Apache Spark Streaming
- Consumes Kafka data.
- Cleans, enriches, and merges streams using time/location windows.
- Computes:
  - `congestion_level`
  - `pollution_risk`
  - `recommended_alternate_routes`
- Outputs enriched results to MongoDB.

### 🗃️ MongoDB
- NoSQL storage for:
  - Real-time data visualization.
  - Historical data archiving.
  - ML model training dataset.

### 📊 Streamlit Dashboard
- Displays:
  - ✅ Live junction status.
  - 🌍 Interactive city map.
  - 📉 Time-series trends.
  - 🔮 Predicted AQI.
  - 🧭 Recommended traffic routes.

---

## 📡 Data Sources & Simulation

| Category | Source                         | Data Fields                               |
|----------|----------------------------------|--------------------------------------------|
| Traffic  | Simulated Python script         | Junction ID, vehicle count, avg speed     |
| AQI      | OpenAQ API / Simulated          | PM2.5, PM10, CO, NO2 levels               |
| Weather  | OpenWeatherMap API / Simulated  | Temperature, humidity, wind speed        |

### Sample APIs:
- [OpenAQ API](https://docs.openaq.org/)
- [OpenWeatherMap API](https://openweathermap.org/api)

---

## 🛠️ Project Setup Guide

### 1. Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. Start Kafka and MongoDB Using Docker Compose
```bash
cd kafka-setup/ && docker-compose up -d
cd mongodb-setup/ && docker-compose up -d
```

### 3. Launch Simulated Data Producers
```bash
python traffic_producer.py
python aqi_producer.py
python weather_producer.py
```

### 4. Start Spark Streaming Job
```bash
spark-submit main_stream.py
```

### 5. Launch the Dashboard
```bash
streamlit run app.py
```

---

## 🔬 Machine Learning (Optional Enhancement)
- Use historical AQI and traffic data to train regression models (e.g., Linear Regression, Random Forest).
- Predict AQI levels for upcoming time windows.
- Display predictions in the dashboard.
- Tools: scikit-learn, pandas, joblib.

---

## 🌱 Future Enhancements

- ✅ Integrate real-time city sensors and IoT devices.
- 📩 Add SMS/email alerts for hazardous pollution levels.
- 🚘 Enhance route optimization using Google Maps or Mapbox APIs.
- 📊 Implement ML-based traffic flow prediction.
- ☁️ Deploy to cloud platforms (AWS/GCP/Azure).

---

## 📌 Tech Stack Summary

| Component         | Tool                      |
|------------------|---------------------------|
| Data Ingestion    | Apache Kafka              |
| Stream Processing | Apache Spark Streaming    |
| Storage           | MongoDB                   |
| Dashboard         | Streamlit                 |
| Containerization  | Docker                    |
| ML (Optional)     | Scikit-learn, Pandas      |
| Language          | Python                    |

---

## 📝 Notes

```bash
⚠️ Make sure your Kafka containers are running before launching the producers.
⚠️ Update the Kafka broker IP address in each producer script.
```

---

## 🐳 Docker Commands (Manual Setup Option)

### Run Zookeeper:
```bash
docker run -p 2181:2181 --name zookeeper zookeeper
```

### Run Kafka Broker:
```bash
$PRIVATE_IP = "192.168.1.5"

docker run -p 9092:9092 `
  -e KAFKA_ZOOKEEPER_CONNECT="$($PRIVATE_IP):2181" `
  -e KAFKA_ADVERTISED_LISTENERS="PLAINTEXT://$($PRIVATE_IP):9092" `
  -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 `
  --name kafka `
  confluentinc/cp-kafka


```

---

## 🏁 Conclusion

This system is a practical example of applying Big Data pipelines to **solve smart city problems in real-time**. By combining streaming, analytics, and machine learning with effective visualization, it creates a blueprint for **data-driven urban governance** and **citizen empowerment**.

