# kafka-consumers/weather_consumer.py

from kafka import KafkaConsumer
import json
import pymongo
from datetime import datetime

# === CONFIG ===
MONGO_URI = "mongodb+srv://uttamseervi:uttamseervi0045*@smartcitycluster.atuzu9o.mongodb.net/?retryWrites=true&w=majority&appName=SmartCityCluster"
KAFKA_BROKER = '192.168.5.218:9092'
TOPIC = 'weather'

# === DB SETUP ===
client = pymongo.MongoClient(MONGO_URI)
db = client['smartcity']
weather_collection = db['weather_data']

# Optional: index to avoid duplicates (timestamp + location)
weather_collection.create_index([("timestamp", 1), ("location", 1)], unique=False)

# === KAFKA CONSUMER ===
consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    auto_offset_reset='latest',
    group_id='weather-consumer',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

# === CONSUMER LOOP ===
for message in consumer:
    try:
        data = message.value

        # Basic validation
        required = ['temperature', 'humidity', 'location']
        if not all(field in data for field in required):
            print("Skipping incomplete weather data:", data)
            continue

        # Enrichment
        data["timestamp"] = datetime.utcnow().isoformat()

        # Insert into MongoDB
        weather_collection.insert_one(data)
        print(f"[✓] Stored weather data: {data}")

    except Exception as e:
        print("[ERROR] Failed to process message:", e)
