import os
from typing import Annotated, Sequence, TypedDict
from dotenv import load_dotenv

# Import the dedicated OpenRouter class
from langchain_openrouter import ChatOpenRouter
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from tools import get_weather, vector_db_search, web_search

load_dotenv()

# Define the State representing Short-Term Memory Context
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

# Define Tools Array
tools_list = [get_weather, vector_db_search, web_search]
tool_node = ToolNode(tools_list)

# Bind system components and LLM using dedicated ChatOpenRouter integration
# The package automatically searches for the OPENROUTER_API_KEY environment variable.
model = ChatOpenRouter(
    model="meta-llama/llama-3.3-70b-instruct", 
    temperature=0
).bind_tools(tools_list)

def call_model(state: AgentState):
    system_prompt = (
        "You are an expert TravelAi Planner who leverages autonomous multi-hop reasoning.\n"
        "If a user proposes a location plan:\n"
        "Hop 1: Query weather codes using appropriate coordinates.\n"
        "Hop 2: Use the returned weather context to perform optimized Vector DB lookups "
        "or fallback web searches to design a perfectly tuned 2-day itinerary.\n"
        "Always communicate constraints based on the weather rules retrieved."
    )
    messages = state["messages"]
    # Ensure system guidance is injected at the start
    if len(messages) == 1:
         messages = [{"role": "system", "content": system_prompt}] + list(messages)
    response = model.invoke(messages)
    return {"messages": [response]}

# Build LangGraph State Framework Workflow
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", tools_condition)
workflow.add_edge("tools", "agent")

# Compile state architecture engine
travel_agent_graph = workflow.compile()