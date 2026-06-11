from tools.tools import get_seasonal_weather_avg, get_weather_by_city, web_search, search_attractions

def test_web_search():
    query = "average flight ticket price from Myanmar to Singapore in December"
    result = web_search(query)
    print(result)

def test_get_weather():
    city = "Yangon"
    result = get_seasonal_weather_avg(city, "July")
    print(result)

def test_search_attractions():
    city = "Tokyo"
    category = "food"
    result = search_attractions(city, category)
    assert "Recommended food spots in Tokyo" in result

if __name__ == "__main__":
    # test_web_search()
    test_get_weather()
    # test_search_attractions()
    # print("All tests passed!")