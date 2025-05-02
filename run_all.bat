@echo off
start cmd /k "python kafka-producers\traffic_producer.py"
start cmd /k "python kafka-producers\weather_producer.py"
start cmd /k "python kafka-consumers\traffic_consumer.py"
start cmd /k "python kafka-consumers\weather_consumer.py"
