import os
import requests
import operator
from typing import TypedDict, Annotated, Sequence
from bs4 import BeautifulSoup
import warnings

# --- LLM Setup ---
# It's better practice to load API keys from environment variables
# or a secure config, but using the provided key for this example.
# Consider using: os.environ.get("GROQ_API_KEY")
api_key = "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" # Replace with your key or load securely

if not api_key:
    raise ValueError("GROQ_API_KEY not set. Please set the environment variable or replace the placeholder.")

from langchain_groq import ChatGroq

llm = ChatGroq(
    # api_key=api_key, # ChatGroq automatically picks up GROQ_API_KEY env var if set
    groq_api_key=api_key, # Explicitly pass if not using env var
    model_name="meta-llama/llama-4-scout-17b-16e-instruct" # Using a recommended model, adjust if needed
    # model_name="meta-llama/llama-4-scout-17b-16e-instruct" # Keep your original if preferred
)

# --- Tool Definition ---
from langchain.tools import Tool
from duckduckgo_search import DDGS

# DuckDuckGo Search wrapper
def duckduckgo_search(query: str) -> list[str]:
    """Runs DuckDuckGo search and returns the top 3 links."""
    print(f"--- Running DuckDuckGo Search for: {query} ---")
    links = []
    try:
        with DDGS() as ddgs:
            # Using ddgs.text for simplicity, consider ddgs.search for more control
            results = ddgs.text(query, max_results=5) # Get a few more just in case some fail
            for r in results:
                if r.get("href"):
                    links.append(r.get("href"))
                if len(links) >= 3:
                    break
    except Exception as e:
        print(f"DuckDuckGo search failed: {e}")
    print(f"--- Found Links: {links} ---")
    return links

# Scrape content from first few links
def fetch_web_content_from_links(links: list[str]) -> str:
    """Fetches and scrapes content from a list of URLs."""
    print(f"--- Fetching content for links: {links} ---")
    texts = []
    for url in links:
        try:
            # Adding headers to mimic a browser
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
            r = requests.get(url, timeout=10, headers=headers)
            r.raise_for_status() # Raise an exception for bad status codes
            soup = BeautifulSoup(r.text, "html.parser")

            # Basic extraction - you might want more sophisticated logic here
            # Remove script and style elements
            for script_or_style in soup(["script", "style"]):
                script_or_style.decompose()

            # Get text, try to remove excessive whitespace
            text = soup.get_text(separator=" ", strip=True)
            # Limit length
            texts.append(text[:2000])
            print(f"--- Successfully scraped: {url} ---")
        except requests.exceptions.RequestException as e:
            print(f"--- Failed to fetch/scrape {url}: {e} ---")
            continue
        except Exception as e:
            print(f"--- Error processing {url}: {e} ---")
            continue # Catch other potential errors during parsing

    if not texts:
        return "No readable content found from the provided links."

    content = "\n\n---\n\n".join(texts)
    print(f"--- Combined Content Length: {len(content)} ---")
    return content

# Combined tool function for LangGraph (Search + Scrape)
def search_and_scrape(query: str) -> str:
    """
    Performs a DuckDuckGo search for the query, retrieves the top 3 links,
    and scrapes the content from those links. Returns the combined scraped text.
    Useful for answering questions requiring up-to-date web information.
    """
    links = duckduckgo_search(query)
    if not links:
        return "Search did not return any usable links."
    content = fetch_web_content_from_links(links)
    return content

# Define the Langchain Tool
web_search_tool = Tool(
    name="WebSearchScraper", # More descriptive name
    func=search_and_scrape,
    description="Searches the web (DuckDuckGo) for a query, fetches content from top results, and returns the combined text. Use this for current events or information not in the LLM's training data."
)

tools = [web_search_tool]

# --- LangGraph Setup ---
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
import operator
from typing import TypedDict, Annotated, Sequence

# Bind tools to the LLM - this allows the LLM to generate structured tool calls
llm_with_tools = llm.bind_tools(tools)

# Define the State for the graph
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

# Define the nodes for the graph

# 1. Call Model Node: Invokes the LLM with the current state (Keep this function as is)
def call_model(state: AgentState):
    """Invokes the LLM with the current message history."""
    print("--- Calling LLM ---")
    messages = state['messages']
    response = llm_with_tools.invoke(messages)
    print(f"--- LLM Response: {response.content[:100]}... (Tool Calls: {hasattr(response, 'tool_calls') and bool(response.tool_calls)}) ---")
    return {"messages": [response]}

# 2. Call Tool Node: REMOVE THE call_tool FUNCTION DEFINITION IF USING ToolNode

# Define the conditional edge logic (Keep this function as is)
def should_continue(state: AgentState) -> str:
    """Determines whether to continue the loop or end."""
    last_message = state['messages'][-1]
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        print("--- Decision: Continue (Tool Call Detected) ---")
        return "continue"
    else:
        print("--- Decision: End (No Tool Call) ---")
        return "end"

# Build the graph
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode # Import ToolNode here

workflow = StateGraph(AgentState)

# Add the nodes
workflow.add_node("agent", call_model)
# workflow.add_node("action", call_tool) # REMOVE this line if using ToolNode
# Add the ToolNode instead
tool_node = ToolNode(tools) # Create the ToolNode
workflow.add_node("action", tool_node) # Add the ToolNode to the graph

# Set the entry point
workflow.set_entry_point("agent")

# Add the conditional edge from 'agent' (Keep this as is)
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "action",
        "end": END
    }
)

# Add the edge from 'action' back to 'agent'
workflow.add_edge("action", "agent")

# Compile the graph into a runnable app
app = workflow.compile()

# --- Running the Graph ---

# Suppress specific LangChain deprecation warnings if necessary (less common with LangGraph)
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain")

# Define the input question
input_question = "is the cmf phone 2 better than nothing phone 2?"
# input_question = "What is the latest news about AI regulations in the EU?" # Example 2

print(f"\n--- Running LangGraph for question: '{input_question}' ---")

# Initial state with the user's question
inputs = {"messages": [HumanMessage(content=input_question)]}

# Invoke the graph stream events for detailed logging (optional)
# print("\n--- Streaming Events ---")
# for event in app.stream(inputs):
#     for k, v in event.items():
#         if k != "__end__": # Exclude the final end marker if desired
#              print(f"Node '{k}':")
#              print(f"  Output: {v}") # v is the output of the node (the state update)
# print("--- Stream Finished ---\n")

# Or just invoke and get the final state
final_state = app.invoke(inputs, {"recursion_limit": 10}) # Add recursion limit

# Extract the final answer (usually the last AI message)
final_answer_message = final_state['messages'][-1]

print("\n--- Final Answer ---")
if isinstance(final_answer_message, AIMessage):
    print(final_answer_message.content)
else:
    print("Could not extract a final AI answer. Last message:", final_answer_message)

# You can also print the full message history for debugging
# print("\n--- Full Message History ---")
# for msg in final_state['messages']:
#     print(f"{msg.type}: {msg.content}")
#     if hasattr(msg, 'tool_calls') and msg.tool_calls:
#         print(f"  Tool Calls: {msg.tool_calls}")