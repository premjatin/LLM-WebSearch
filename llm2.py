import os
import requests
import operator
from typing import TypedDict, Annotated, Sequence
from bs4 import BeautifulSoup
import warnings

# --- LLM Setup --- (Keep as is)
api_key = "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"
if not api_key: raise ValueError("GROQ_API_KEY not set.")
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain.tools import Tool
from duckduckgo_search import DDGS
llm = ChatGroq(groq_api_key=api_key, model_name="llama3-70b-8192")

# --- Tool Definition --- (Keep as is)
def duckduckgo_search(query: str) -> list[str]:
    print(f"--- Running DuckDuckGo Search for: {query} ---")
    links = []
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=5); links = [r['href'] for r in results if r.get('href')][:3]
    except Exception as e: print(f"DuckDuckGo search failed: {e}")
    print(f"--- Found Links: {links} ---"); return links
def fetch_web_content_from_links(links: list[str]) -> str:
    print(f"--- Fetching content for links: {links} ---"); texts = []
    for url in links:
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}; r = requests.get(url, timeout=10, headers=headers); r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            for script_or_style in soup(["script", "style"]): script_or_style.decompose()
            text = soup.get_text(separator=" ", strip=True); texts.append(text[:2500])
            print(f"--- Successfully scraped: {url} ---")
        except Exception as e: print(f"--- Failed to fetch/scrape {url}: {e} ---")
    if not texts: return "No readable content found."; content = "\n\n---\n\n".join(texts)
    print(f"--- Combined Content Length: {len(content)} ---"); return content
def search_and_scrape(query: str) -> str:
    links = duckduckgo_search(query);
    if not links: return "Search did not return any usable links."
    return fetch_web_content_from_links(links)
web_search_tool = Tool(name="WebSearchScraper", func=search_and_scrape, description="Searches web, fetches content. Use for current info.")
tools = [web_search_tool]

# --- LangGraph Setup ---
llm_with_tools = llm.bind_tools(tools)
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]; elaboration_count: int
# === NODES === (Keep call_model and request_elaboration as is)
def call_model(state: AgentState):
    print(f"--- Calling LLM (Elaboration Count: {state.get('elaboration_count', 0)}) ---"); messages = state['messages']
    response = llm_with_tools.invoke(messages)
    print(f"--- LLM Response: {response.content[:100]}... (Tool Calls: {hasattr(response, 'tool_calls') and bool(response.tool_calls)}) ---")
    return {"messages": [response]}
def request_elaboration(state: AgentState):
    print("--- Adding Elaboration Request ---"); last_ai_message = ""
    for msg in reversed(state['messages']):
        if isinstance(msg, AIMessage) and (not hasattr(msg, 'tool_calls') or not msg.tool_calls): last_ai_message = msg.content; break
    elaboration_prompt_text = f"That's helpful. Please elaborate further on key aspects using the search results provided earlier. Expand beyond this summary:\n'{last_ai_message}'"
    elaboration_prompt = HumanMessage(content=elaboration_prompt_text)
    current_count = state.get('elaboration_count', 0)
    return {"messages": [elaboration_prompt], "elaboration_count": current_count + 1}
from langgraph.prebuilt import ToolNode
tool_node = ToolNode(tools)
# === MODIFIED CONDITIONAL LOGIC === (Keep route_after_agent as is)
def route_after_agent(state: AgentState) -> str:
    last_message = state['messages'][-1]; elaboration_count = state.get('elaboration_count', 0)
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls: print("--- Decision: Route to Action ---"); return "action"
    elif elaboration_count < 1: print(f"--- Decision: Route to Request Elaboration (Count: {elaboration_count}) ---"); return "request_elaboration"
    else: print(f"--- Decision: Route to End (Elaboration Count: {elaboration_count}) ---"); return "end"
# === Build the graph === (Keep graph definition as is)
from langgraph.graph import StateGraph, END
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model); workflow.add_node("action", tool_node); workflow.add_node("request_elaboration", request_elaboration)
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", route_after_agent, {"action": "action", "request_elaboration": "request_elaboration", "end": END})
workflow.add_edge("action", "agent"); workflow.add_edge("request_elaboration", "agent")

# Compile the graph (Corrected - no recursion_limit here)
app = workflow.compile(checkpointer=None)

# --- Running the Graph ---
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain")

input_question = "What is the latest news about AI regulations in the EU?"
print(f"\n--- Running LangGraph for question: '{input_question}' ---")

inputs = {"messages": [HumanMessage(content=input_question)], "elaboration_count": 0}
config = {"recursion_limit": 15} # Define config dictionary

# === MODIFIED EXECUTION: Use invoke() ===
print("\n--- Invoking Graph ---")
# final_state will contain the complete AgentState after execution
final_state = app.invoke(inputs, config=config)
print("--- Invocation Complete ---")

# --- Keep Streaming Code Commented for Debugging (Optional) ---
# print("\n--- Streaming Events ---")
# final_state_from_stream = None # Variable to hold the state data from the last relevant event
# for event in app.stream(inputs, config=config):
#     for node_name, output in event.items():
#         print(f"Node '{node_name}':")
#         if isinstance(output, dict):
#              print(f"  State Updated: {list(output.keys())}")
#              final_state_from_stream = output # Capture the latest state update
#              if 'messages' in output and output['messages']:
#                  last_msg = output['messages'][-1]
#                  print(f"    -> Last Message Type: {type(last_msg).__name__}")
#                  if hasattr(last_msg, 'content'): print(f"    -> Content Preview: {str(last_msg.content)[:150]}...")
#                  if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls: print(f"    -> Tool Calls: {last_msg.tool_calls}")
#         else: print(f"  Output: {output}")
# print("--- Stream Finished ---\n")
# final_state = final_state_from_stream # Use the state captured from the stream
# --- End of Commented Streaming Code ---


# === PROCESS FINAL STATE ===
print("\n--- Processing Final State ---")
# print(final_state) # Uncomment to see the raw final state dict

# Extract and print the final answer from the state returned by invoke()
if final_state and isinstance(final_state, dict) and 'messages' in final_state:
    final_answer_message = final_state['messages'][-1]
    print("\n--- Final Answer ---")
    # The very last message should be the AI's elaborated answer
    if isinstance(final_answer_message, AIMessage):
        print(final_answer_message.content)
    else:
        # Fallback: Check second-to-last message if the last isn't AI (less likely now)
        if len(final_state['messages']) > 1 and isinstance(final_state['messages'][-2], AIMessage):
             print(final_state['messages'][-2].content)
        else:
             print("Could not extract a final AI answer. Last message:", final_answer_message)
else:
     print(f"Could not retrieve final state messages. Final state was: {final_state}")


# Optional: Print full history
# print("\n--- Full Message History ---")
# if final_state and isinstance(final_state, dict) and 'messages' in final_state:
#     for msg in final_state['messages']:
#         print(f"{msg.type}: {str(msg.content)[:300]}...")
#         if hasattr(msg, 'tool_calls') and msg.tool_calls: print(f"  Tool Calls: {msg.tool_calls}")