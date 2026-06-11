import requests
from tools.params_and_wmo import WMO_CODE_MAP, COORDS_URL, params

def interpret_weather_code(code: int) -> dict:
    """
    Translates a numeric WMO weather code from Open-Meteo into a 
    structured, human-readable dictionary block.
    """
    # Safe fallback if the code is unknown or missing
    target_code = int(code) if code is not None else 0
    
    code_info = WMO_CODE_MAP.get(target_code, {
        "description": "Unknown conditions", 
        "condition": "unknown"
    })
    
    return {
        "raw_code": target_code,
        "description": code_info["description"],
        "condition": code_info["condition"],
        "requires_indoor_plan": code_info["condition"] in ["rain", "storm", "snow"]
    }

def get_coordinates(city_name: str) -> dict:
    """
    Converts a city name into latitude, longitude, and country information
    using the free Open-Meteo Geocoding API.
    """    
    try:
        response = requests.get(COORDS_URL, params=params["coords_param"] | {"name": city_name})
        response.raise_for_status()
        data = response.json()
        
        # Check if any results were found
        results = data.get("results")
        if not results:
            return {"error": f"Could not find coordinates for city: '{city_name}'"}
            
        top_result = results[0]
        return {
            "latitude": top_result.get("latitude"),
            "longitude": top_result.get("longitude"),
            "city": top_result.get("name"),
            "country": top_result.get("country")
        }
    except Exception as e:
        return {"error": f"Geocoding API request failed: {str(e)}"}