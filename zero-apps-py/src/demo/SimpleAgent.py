from langchain.agents import initialize_agent, load_tools
from langchain_openai import ChatOpenAI

# STEP 1: Load GPT model
llm = ChatOpenAI(model_name="gpt-4", temperature=0)

# STEP 2: Load tools
tools = load_tools(["serpapi", "llm-math"], llm=llm)  # Requires SerpAPI key for search

# STEP 3: Create the agent
agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True)

# STEP 4: Ask the agent to perform tasks
response = agent.run(
    "Search for the current population of India, then divide it by 10 million."
)

print("Agent Response:", response)