LangSmith is LangChain’s developer platform designed to build, test, debug, and monitor AI applications at scale.

While LangChain provides the framework to build LLM-powered apps, LangSmith adds production-grade tools for:

Tracing executions (like a debugger for LLMs).

Evaluating model performance with metrics.

Monitoring real-time usage and errors.

Comparing multiple LLMs or prompt versions.

Managing datasets and test cases.

Think of LangSmith as “GitHub + Datadog + Postman for LangChain apps”.

1. Why LangSmith is Useful

When building LLM-powered applications, you often face challenges like:

Challenge	How LangSmith Helps
Hard to debug model outputs	Provides execution traces step-by-step.
Prompt changes breaking behavior	Track prompt versions and compare outputs.
No visibility into failures	Monitor real-time errors and logs.
Testing new models is manual	Run A/B tests on different LLMs.
Evaluating performance	Built-in evaluation metrics (accuracy, latency, cost).
2. LangChain vs LangSmith
Aspect	LangChain (Framework)	LangSmith (Platform)
Purpose	Build AI workflows & chains	Debug, monitor, evaluate
Code execution	Runs in your environment	Hosted dashboard
Tracing	Manual logging	Automatic step-by-step tracing
Model testing	Limited	Built-in evaluation tools
Collaboration	Code-only	Web interface for team use

How they work together:

LangChain builds the logic and agent workflows.

LangSmith tracks, monitors, and optimizes these workflows in production.

3. LangSmith Core Features
a) Tracing (Debugging Tool)

Like a debugger for AI apps:

See every step your LangChain agent takes.

Inspect prompts, intermediate outputs, and final responses.

Identify where failures happen.

Example:
If a chatbot gives a wrong answer, LangSmith shows:

The prompt sent to GPT.

The model’s raw output.

The retriever search results.

Which tool the agent decided to call.

b) Evaluation & Testing

You can:

Create datasets of test inputs (like QA pairs).

Automatically run them against different models or prompts.

See performance metrics:

Accuracy

Latency

Token usage

Cost

This helps with A/B testing when choosing between models like GPT-4 vs Claude.

c) Real-Time Monitoring

View production traffic live.

Track latency and cost per request.

Detect failure patterns early.

This is critical for scaling enterprise apps.

d) Collaboration

Team members can share traces and experiment results via the LangSmith UI.

Similar to sharing logs or dashboards.

4. Setting Up LangSmith
Step 1: Create a LangSmith Account

Sign up at https://smith.langchain.com/
.

Create a project and get an API key.

Step 2: Install LangChain with LangSmith Support
pip install langchain langsmith

Step 3: Configure Environment Variables

Set your keys securely.

For Linux / Mac:

export LANGCHAIN_API_KEY="your-langsmith-api-key"
export LANGCHAIN_TRACING_V2="true"
export LANGCHAIN_PROJECT="MyFirstProject"


For Windows (PowerShell):

setx LANGCHAIN_API_KEY "your-langsmith-api-key"
setx LANGCHAIN_TRACING_V2 "true"
setx LANGCHAIN_PROJECT "MyFirstProject"

Step 4: Update Your LangChain Code

Here’s an updated RetrievalQA example with LangSmith tracing enabled:

import os
from langchain_openai import ChatOpenAI
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langsmith import traceable

# Load environment variables
os.environ["OPENAI_API_KEY"] = "sk-xxxxxxxxxxxxxxxxxxxx"
os.environ["LANGCHAIN_API_KEY"] = "ls-xxxxxxxxxxxxxxxxxxxx"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "MyFirstProject"

# Load document
loader = TextLoader("data.txt")
documents = loader.load()

# Split text
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
docs = text_splitter.split_documents(documents)

# Create vector store
from langchain_openai import OpenAIEmbeddings
embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(docs, embeddings)

# Create chain
llm = ChatOpenAI(model_name="gpt-4", temperature=0)
qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=vectorstore.as_retriever())

@traceable(run_type="query")
def answer_query(query: str):
    return qa_chain.invoke({"query": query})

# Run query
response = answer_query("What services does TravelAI offer?")
print(response["result"])

5. Viewing Traces

Run your code.

Go to LangSmith dashboard
.

Open your project.

You’ll see:

Each query.

Each step the chain took.

Timing, cost, and intermediate data.

6. Architecture Diagram
[User Input] 
    ↓
[LangChain App: Chains, Agents]
    ↓
[LangSmith Tracing Layer]
    ↓
[OpenAI or other LLM APIs]
    ↓
[LangSmith Dashboard: Logs, Monitoring, Evaluation]

7. When to Use LangSmith

LangSmith is ideal when:

You have multiple prompts and models and need to test them systematically.

You are deploying to production and want observability.

Your AI app interacts with multiple external APIs and you need to debug failures.

You work in a team environment and need to share insights.

Summary
LangSmith Feature	Why It Matters
Tracing	Debug your AI step-by-step
Evaluation & Testing	Measure performance before deployment
Monitoring & Analytics	Track latency, cost, and failures
Collaboration	Share logs and test results

LangChain builds AI workflows, and LangSmith helps you manage, debug, and optimize them for production.