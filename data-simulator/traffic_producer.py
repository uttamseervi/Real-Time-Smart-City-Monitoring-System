# data-simulator/traffic_producer.py
from kafka import KafkaProducer
import json
import time
import random
from datetime import datetime

producer = KafkaProducer(bootstrap_servers='localhost:9093', value_serializer=lambda v: json.dumps(v).encode('utf-8'))

def generate_traffic_data():
    junctions = ["Connaught Place", "Indira Gandhi International Airport", "New Delhi Railway Station"]
    while True:
        traffic_data = {
            "junction": random.choice(junctions),
            "timestamp": datetime.utcnow().isoformat(),
            "vehicles_per_minute": random.randint(80, 200),
            "avg_speed_kmph": random.randint(5, 40)
        }
        producer.send('traffic-data', traffic_data)
        print(f"Sent traffic data: {traffic_data}")
        time.sleep(1)  # Simulate sending data every second

if __name__ == "__main__":
    generate_traffic_data()
