import os
from dotenv import load_dotenv
from tools.tools import get_seasonal_weather_avg, get_weather_by_city, vector_db_search, web_search
from tools.ingest import run_ingestion

load_dotenv(".env.secret")
def test_web_search():
    query = "average flight ticket price from Myanmar to Singapore in December"
    result = web_search(query)
    print(result)

def test_get_weather():
    city = "Yangon"
    result = get_seasonal_weather_avg(city, "July")
    print(result)

def test_vector_db_search():
    query = "What are the top attractions in Bali?"
    result = vector_db_search(query)
    print(result)

if __name__ == "__main__":
    # run_ingestion()  # Ensure the vector database is populated before testing search
    # test_web_search()
    # test_get_weather()
    test_vector_db_search()
    # test_search_attractions()
    # print("All tests passed!")