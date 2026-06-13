from langchain_openrouter import ChatOpenRouter
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from tools.tools import get_weather_by_city, vector_db_search, web_search, get_seasonal_weather_avg

# Define tools list
tools_list = [get_weather_by_city, get_seasonal_weather_avg, vector_db_search, web_search]

# ChatOpenRouter Initialization
model = ChatOpenRouter(
    model="openai/gpt-4o-mini",
    temperature=0,
    max_retries=1,
)

system_prompt = (
    "You are an expert TravelAi Planner who leverages autonomous multi-hop reasoning.\n"
    "Use the provided tools to gather information, analyze options, and create personalized travel itineraries based on user preferences and constraints.\n"
    "Always think step-by-step, and if you need specific data (like weather forecasts, local insights, or historical trends), invoke the relevant tool to fetch that information before proceeding with your reasoning."
)

# Initialize MemorySaver to persist checkpoints across execution cycles
memory_checkpointer = MemorySaver()

# Pass checkpointer into the prebuilt ReAct agent
travel_agent_graph = create_react_agent(
    model, 
    tools=tools_list, 
    prompt=system_prompt,
    checkpointer=memory_checkpointer # Activates out-of-the-box conversational state preservation
)