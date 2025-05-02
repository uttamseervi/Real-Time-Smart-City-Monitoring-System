# kafka-consumers/traffic_consumer.py

from kafka import KafkaConsumer
import json
import pymongo
from datetime import datetime

# === CONFIG ===
MONGO_URI = "mongodb+srv://uttamseervi:uttamseervi0045*@smartcitycluster.atuzu9o.mongodb.net/?retryWrites=true&w=majority&appName=SmartCityCluster"
KAFKA_BROKER = '192.168.5.218:9092'
TOPIC = 'traffic'

# === DB SETUP ===
client = pymongo.MongoClient(MONGO_URI)
db = client['smartcity']
traffic_collection = db['traffic_data']

# Optional: ensure index for deduplication
traffic_collection.create_index([("timestamp", 1), ("frc", 1)], unique=False)

# === KAFKA CONSUMER ===
consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    auto_offset_reset='latest',
    group_id='traffic-consumer',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

# === ENRICHMENT FUNCTION ===
def classify_congestion(vehicles_per_minute):
    if vehicles_per_minute is None:
        return "unknown"
    elif vehicles_per_minute > 300:
        return "severe"
    elif vehicles_per_minute > 150:
        return "high"
    elif vehicles_per_minute > 50:
        return "medium"
    else:
        return "low"

# === CONSUMER LOOP ===
for message in consumer:
    try:
        data = message.value

        # Validation
        if 'currentSpeed' not in data or 'freeFlowSpeed' not in data:
            print("Skipping invalid message:", data)
            continue

        # Enrichment
        data['congestion_level'] = classify_congestion(data.get('vehicles_per_minute'))
        data['timestamp'] = datetime.utcnow().isoformat()

        # Insert into MongoDB
        traffic_collection.insert_one(data)
        print(f"[✓] Stored traffic data: {data}")

    except Exception as e:
        print("[ERROR] Failed to process message:", e)
