db.createCollection("traffic_data");
db.createCollection("aqi_data");
db.createCollection("weather_data");

// Example indexes for optimization
db.traffic_data.createIndex({ "timestamp": 1 });
db.aqi_data.createIndex({ "timestamp": 1 });
db.weather_data.createIndex({ "timestamp": 1 });
