import requests
from kafka import KafkaProducer
import json
import time

# Kafka Config
KAFKA_BROKER = '192.168.5.218:9092'
TOPIC_NAME = 'weather'

# OpenWeatherMap API Config
API_KEY = '71b7ad91a96968872851dec68a282946'
LAT =  12.9527125 
LON =  76.5770888 
URL = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}"

# Kafka Producer Setup
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def fetch_weather_data():
    response = requests.get(URL)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to fetch weather data:", response.status_code)
        return None
def parse_weather_data(data):
    parsed = {}
    try:
        parsed['location'] = data.get('name', 'unknown')
        parsed['temperature'] = data['main']['temp']
        parsed['feels_like'] = data['main']['feels_like']
        parsed['humidity'] = data['main']['humidity']
        parsed['pressure'] = data['main']['pressure']
        parsed['wind_speed'] = data['wind']['speed']
        parsed['weather'] = data['weather'][0]['main']
        parsed['description'] = data['weather'][0]['description']
        parsed['timestamp'] = data['dt']
    except Exception as e:
        print("Error parsing weather data:", e)
    return parsed

def produce():
    while True:
        raw_data = fetch_weather_data()
        if raw_data:
            parsed_data = parse_weather_data(raw_data)
            producer.send(TOPIC_NAME, parsed_data)
            print("Weather data sent to Kafka:", parsed_data)
        time.sleep(10)  # API rate limit safe zone

if __name__ == "__main__":
    produce()
