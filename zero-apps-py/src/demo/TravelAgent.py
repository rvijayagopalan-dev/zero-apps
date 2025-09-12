from langchain.agents import initialize_agent, Tool
from langchain_openai import ChatOpenAI
import os

import dotenv
dotenv.load_dotenv()

# STEP 1: Define custom tools
def check_weather(city: str) -> str:
    return f"The weather in {city} is sunny with 28°C."  # Replace with real API call

def search_flights(destination: str) -> str:
    return f"Flights to {destination} start at $350."  # Replace with real API call

tools = [
    Tool(name="Weather API", func=check_weather, description="Checks weather of a city"),
    Tool(name="Flight Search API", func=search_flights, description="Searches flights for a destination")
]

# STEP 2: Create GPT agent
llm = ChatOpenAI(model_name="gpt-4", temperature=0, openai_api_key=os.getenv("OPENAI_API_KEY"))  # Optional if already in environment)
agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True)

# STEP 3: Run a query
response = agent.run("Plan a weekend trip to Goa, check the weather and find flights.")
print("Trip Planner:", response)
