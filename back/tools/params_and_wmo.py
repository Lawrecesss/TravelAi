# Mappings for the WMO interpretation codes used by Open-Meteo
WMO_CODE_MAP = {
    0: {"description": "Clear sky", "condition": "clear"},
    1: {"description": "Mainly clear", "condition": "clear"},
    2: {"description": "Partly cloudy", "condition": "cloudy"},
    3: {"description": "Overcast", "condition": "cloudy"},
    45: {"description": "Fog", "condition": "foggy"},
    48: {"description": "Depositing rime fog", "condition": "foggy"},
    51: {"description": "Light drizzle", "condition": "rain"},
    53: {"description": "Moderate drizzle", "condition": "rain"},
    55: {"description": "Dense drizzle", "condition": "rain"},
    56: {"description": "Light freezing drizzle", "condition": "rain"},
    57: {"description": "Dense freezing drizzle", "condition": "rain"},
    61: {"description": "Slight rain", "condition": "rain"},
    63: {"description": "Moderate rain", "condition": "rain"},
    65: {"description": "Heavy rain", "condition": "rain"},
    66: {"description": "Light freezing rain", "condition": "rain"},
    67: {"description": "Heavy freezing rain", "condition": "rain"},
    71: {"description": "Slight snow fall", "condition": "snow"},
    73: {"description": "Moderate snow fall", "condition": "snow"},
    75: {"description": "Heavy snow fall", "condition": "snow"},
    77: {"description": "Snow grains", "condition": "snow"},
    80: {"description": "Slight rain showers", "condition": "rain"},
    81: {"description": "Moderate rain showers", "condition": "rain"},
    82: {"description": "Violent rain showers", "condition": "rain"},
    85: {"description": "Slight snow showers", "condition": "snow"},
    86: {"description": "Heavy snow showers", "condition": "snow"},
    95: {"description": "Thunderstorm", "condition": "storm"},
    96: {"description": "Thunderstorm with slight hail", "condition": "storm"},
    99: {"description": "Thunderstorm with heavy hail", "condition": "storm"}
}

WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
COORDS_URL = "https://geocoding-api.open-meteo.com/v1/search"
PAST_WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"

HISTORICAL_YEARS         = 5
RAINY_DAY_THRESHOLD_MM   = 1.0

params = {
    "weather_param": {
        "current_weather": "true",
        "daily": "weathercode, temperature_2m_mean,temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "auto"
    },
    "coords_param": {
        "count": 1,        
        "language": "en"
    },
    "historical_param": {
        "daily": "temperature_2m_mean,temperature_2m_max,temperature_2m_min,"
                 "precipitation_sum,weather_code",
        "timezone": "auto"
    }
}