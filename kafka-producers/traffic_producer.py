import requests
import xml.etree.ElementTree as ET
from kafka import KafkaProducer
import json
import time

# Kafka Config
KAFKA_BROKER = '192.168.5.218:9092'
TOPIC_NAME = 'traffic'

# TomTom API Config
'''
API-KEY
https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/xml?key=jAPkpwt8b2gxLgAGQkyvGN7Bchz88x0v&point=52.41072,4.84239'''

API_KEY = 'jAPkpwt8b2gxLgAGQkyvGN7Bchz88x0v'
LAT = 52.41072
LON = 4.84239
URL = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/xml?key={API_KEY}&point={LAT},{LON}"

# Set up Kafka Producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def fetch_traffic_data():
    response = requests.get(URL)
    if response.status_code == 200:
        return ET.fromstring(response.content)
    else:
        print("Failed to fetch data:", response.status_code)
        return None

def parse_traffic_data(xml_root):
    data = {}
    try:
        data['frc'] = xml_root.find('frc').text
        data['currentSpeed'] = float(xml_root.find('currentSpeed').text)
        data['freeFlowSpeed'] = float(xml_root.find('freeFlowSpeed').text)
        data['currentTravelTime'] = int(xml_root.find('currentTravelTime').text)
        data['freeFlowTravelTime'] = int(xml_root.find('freeFlowTravelTime').text)
        data['confidence'] = float(xml_root.find('confidence').text)
        data['roadClosure'] = xml_root.find('roadClosure').text.lower() == 'true'
        # Add more as needed
    except Exception as e:
        print("Error parsing XML:", e)
    return data

def produce():
    while True:
        xml_data = fetch_traffic_data()
        if xml_data:
            parsed_data = parse_traffic_data(xml_data)
            producer.send(TOPIC_NAME, parsed_data)
            print("Data sent to Kafka:", parsed_data)
        time.sleep(10)  # Adjust as needed for API rate limits

if __name__ == "__main__":
    produce()
