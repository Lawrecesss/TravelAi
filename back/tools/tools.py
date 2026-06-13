# tools.py
import calendar
from collections import Counter
import os
import datetime
from langchain_core.tools import tool
import requests
from tavily import TavilyClient
from pinecone import Pinecone
from tools.weather_helper import interpret_weather_code, get_coordinates
from tools.params_and_wmo import HISTORICAL_YEARS, PAST_WEATHER_URL, RAINY_DAY_THRESHOLD_MM, WEATHER_URL, params

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

@tool
def web_search(query: str) -> str:
    """
    Useful for retrieving real-time information on flight prices, local events, or any rapidly changing travel details that may not be captured in the static knowledge base.
    Search the web for up-to-date travel blogs, itineraries, and local insights.
    Input should be a natural language query related to travel planning (e.g., "average flight ticket price from Myanmar to Singapore in December" or "current COVID-19 restrictions in Tokyo").
    This tool uses the Tavily API to perform a web search and returns the most relevant answer or information snippet to the agent for use in itinerary planning or answering user questions.
    """
    response = tavily_client.search(query=query, search_depth="basic", include_answer=True) #later chenge to "advance" for better results
    return response["answer"] if "answer" in response else "No results found. Please try a different query."
    # return response["results"][0]["content"] if response["results"] else "No results found. Please try a different query."
    
@tool
def get_weather_by_city(city_name: str) -> dict:
    """
    Useful when you need to get the current weather or a 7-day forecast 
    for a specific city. Input should be a city name (e.g., 'Paris', 'Tokyo').
    """
    # Resolve the city name to lat/long coordinates 
    coords = get_coordinates(city_name)
    
    # If the helper returned an error (e.g., city not found), pass it back to the agent
    if "error" in coords:
        return coords
    try:
        response = requests.get(WEATHER_URL, params=params["weather_param"] | {"latitude": coords["latitude"], "longitude": coords["longitude"]})
        response.raise_for_status()
        weather_data = response.json()
        # print(weather_data)
        return {
            "location": f"{coords['city']}, {coords['country']}",
            "latitude": coords["latitude"],
            "longitude": coords["longitude"],
            "current_weather": interpret_weather_code(weather_data.get("current_weather", {}).get("wmo_code")),
            "forecast": {
                "days": weather_data.get("daily", {}).get("time", []),
                "weather_codes": [interpret_weather_code(code) for code in weather_data.get("daily", {}).get("weather_code", [])],
                "indoor_plan_recommendations": [interpret_weather_code(code)["requires_indoor_plan"] for code in weather_data.get("daily", {}).get("weather_code", [])],
                "temp_mean": weather_data.get("daily", {}).get("temperature_2m_mean", []),
                "temp_max": weather_data.get("daily", {}).get("temperature_2m_max", []),
                "temp_min": weather_data.get("daily", {}).get("temperature_2m_min", []),
                "precipitation_sum": weather_data.get("daily", {}).get("precipitation_sum", [])
            },
            "note": "Current weather and 7-day forecast data sourced from Open-Meteo API, interpreted using WMO codes for condition summaries and indoor plan recommendations." 
        }
    except Exception as e:
        return {"error": f"Failed to fetch weather data: {str(e)}"}
    
@tool
def get_seasonal_weather_avg(city: str, month: str) -> dict:
    """
    Useful when you need to get the typical weather conditions for a specific city and month based on historical data.
    Input should be a city name and a month (e.g., 'Tokyo', 'December').
    Queries Open-Meteo's Historical API across past years to find the most frequent
    WMO weather code alongside average temperature and precipitation metrics.
    """
    coords = get_coordinates(city)
    if "error" in coords:
        return coords

    try:
        month_num = datetime.datetime.strptime(month.strip(), "%B").month
    except ValueError:
        return {"error": f"Invalid month format '{month}'. Use full names like 'December'."}

    current_year = datetime.datetime.now().year
    past_years = list(range(current_year - HISTORICAL_YEARS, current_year))  # consistent with get_weather_by_month

    all_wmo_codes:   list[int]   = []
    all_temp_mean:   list[float] = []
    all_temp_min:    list[float] = []
    all_temp_max:    list[float] = []
    all_precip:      list[float] = []

    try:
        for year in past_years:
            # Compute end_date correctly using only datetime.date (no mixing)
            start_date = datetime.date(year, month_num, 1)
            end_date   = datetime.date(
                year,
                month_num,
                calendar.monthrange(year, month_num)[1]  # handles leap years too
            )

            response = requests.get(
                PAST_WEATHER_URL,
                params=params["historical_param"] | {
                    "latitude":   coords["latitude"],
                    "longitude":  coords["longitude"],
                    "start_date": start_date.isoformat(),
                    "end_date":   end_date.isoformat(),
                }
            )
            response.raise_for_status()
            daily = response.json().get("daily", {})

            all_wmo_codes.extend(int(w) for w in daily.get("weather_code",       []) if w is not None)
            all_temp_mean.extend(v      for v in daily.get("temperature_2m_mean", []) if v is not None)
            all_temp_min.extend( v      for v in daily.get("temperature_2m_min",  []) if v is not None)
            all_temp_max.extend( v      for v in daily.get("temperature_2m_max",  []) if v is not None)
            all_precip.extend(   v      for v in daily.get("precipitation_sum",   []) if v is not None)

        if not all_wmo_codes or not all_temp_mean or not all_precip or not all_temp_min or not all_temp_max:
            return {"error": "Could not extract consistent historical baselines."}

        most_common_wmo   = Counter(all_wmo_codes).most_common(1)[0][0]
        weather           = interpret_weather_code(most_common_wmo)

        return {
            "location":                   f"{coords['city']}, {coords['country']}",
            "requested_month":            month.capitalize(),
            "data_source":                "historical_average",        # consistent with get_weather_by_month
            "horizon_type":               f"Historical Climate Baseline ({HISTORICAL_YEARS}-Year Average)",
            "dominant_wmo_code":          weather["raw_code"],
            "condition_summary":          weather["description"],
            "indoor_plan_recommendation": weather["requires_indoor_plan"],
            "temp_avg":                   round(sum(all_temp_mean) / len(all_temp_mean), 1) if all_temp_mean else None,
            "temp_min_avg":               round(sum(all_temp_min)  / len(all_temp_min),  1) if all_temp_min  else None,
            "temp_max_avg":               round(sum(all_temp_max)  / len(all_temp_max),  1) if all_temp_max  else None,
            "precipitation_total_avg":    round(sum(all_precip) / HISTORICAL_YEARS, 1)               if all_precip    else None,
            "rainy_days_avg":             round(sum(1 for p in all_precip if p >= RAINY_DAY_THRESHOLD_MM) / HISTORICAL_YEARS, 1),
            "note": (
                f"Dominant weather pattern and averages computed from {HISTORICAL_YEARS} years of "
                f"historical data ({past_years[0]}–{past_years[-1]}) for {month.capitalize()}."
            ),
        }

    except Exception as e:
        return {"error": f"Historical baseline calculation failed: {str(e)}"}

@tool
def vector_db_search(query: str) -> str:
    """
    Useful for retrieving localized, contextually relevant information from the curated knowledge base during itinerary planning or when answering specific questions about a destination, budget considerations, activities.
    Input should be a natural language query related to travel planning (e.g., "What are the top attractions in Bali?" or "Give me budget tips for Tokyo.").
    This tool performs a vector similarity search against the Pinecone index where the curated knowledge base is stored, returning the most relevant text chunks as context for the agent's response generation.
    """
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))
    
    # Runtime context matching query needs input_type="query"
    embedding_res = pc.inference.embed(
        model="llama-text-embed-v2",
        inputs=[query],
        parameters={"input_type": "query"}
    )
    query_vector = embedding_res.data[0].values
    results = index.query(vector=query_vector, top_k=3, include_metadata=True)
    # print(f"Vector DB Search Results for query: '{query}'\n{results}\n")
    matched_contexts = []
    for match in results.get("matches", []):
        if "chunk" in match.get("metadata", {}):
            matched_contexts.append(match["metadata"]["chunk"])
            
    if not matched_contexts:
        return "No local curated knowledge records found for this location matrix query."
        
    return "\n---\n".join(matched_contexts)