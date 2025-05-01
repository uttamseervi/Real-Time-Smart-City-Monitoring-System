# import requests

# API_KEY = '15ffecc7d19e313834eec98ce4104e33d2ffbc0d5f7995edca4b91a3f942958d'
# LOCATION_ID = 2178  # Replace this with the actual location ID you're interested in

# def fetch_location_info():
#     url = f"https://api.openaq.org/v3/locations/{LOCATION_ID}"
#     headers = {
#         "X-API-Key": API_KEY
#     }

#     response = requests.get(url, headers=headers)

#     if response.status_code == 200:
#         return response.json()
#     else:
#         print(f"Failed to fetch location data. Status code: {response.status_code}")
#         return None

# # Example usage
# if __name__ == "__main__":
#     data = fetch_location_info()
#     if data:
#         print("Location Info:", data)

import requests
import json
from kafka import KafkaProducer
import time

# Kafka Config
KAFKA_BROKER = 'localhost:9092'  # Update this with your Kafka broker's address
TOPIC_NAME = 'aqi_data'

# OpenAQ API Config
API_KEY = '15ffecc7d19e313834eec98ce4104e33d2ffbc0d5f7995edca4b91a3f942958d'
LOCATION_ID = 2178  # Change this if you need a different location

def fetch_aqi_data():
    """Fetch air quality data from OpenAQ API."""
    url = f"https://api.openaq.org/v3/measurements?location_id={LOCATION_ID}&limit=10"
    headers = {"X-API-Key": API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        print("Data fetched successfully", response.json())
        return response.json()['results']
    else:
        print(f"Error fetching data: {response.status_code}")
        return []

def produce():
    """Fetch AQI data and send it to Kafka continuously."""
    # Set up Kafka Producer
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    
    while True:
        aqi_data = fetch_aqi_data()
        if aqi_data:
            for item in aqi_data:
                # Send each AQI data point to Kafka topic
                producer.send(TOPIC_NAME, item)
                print(f"Data sent to Kafka: {item}")
        else:
            print("No data fetched.")
        
        time.sleep(10)  # Adjust as needed for API rate limits

if __name__ == "__main__":
    produce()
