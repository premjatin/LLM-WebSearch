import operator
from typing import TypedDict, Annotated, Sequence

from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from app.agent.tools import agent_tools # Import the combined list of tools
from app.core.config import settings
from langchain_groq import ChatGroq

# Initialize LLM
llm = ChatGroq(
    groq_api_key=settings.groq_api_key,
    model_name="llama3-70b-8192", # Or your preferred model
    temperature=0.1 # Adjust temperature as needed
)

# Bind tools to the LLM. The order might influence preference, but descriptions are key.
llm_with_tools = llm.bind_tools(agent_tools)

# Define the State
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # You could add more state here if needed, e.g., conversation_id, user_info

# Define Nodes

# 1. Agent Node: Calls the LLM
def call_model(state: AgentState):
    """Invokes the LLM with the current message history."""
    print(f"--- Calling LLM ---")
    messages = state['messages']
    # Crucially use the LLM with tools bound here
    response = llm_with_tools.invoke(messages)
    print(f"--- LLM Response: {response.content[:100]}... (Tool Calls: {hasattr(response, 'tool_calls') and bool(response.tool_calls)}) ---")
    # The response object will include AIMessage content and potentially tool_calls
    return {"messages": [response]}

# 2. Action Node: Executes tools
# Use the prebuilt ToolNode which handles executing tools based on AIMessage.tool_calls
tool_node = ToolNode(agent_tools)


# Define Conditional Edge Logic
def should_continue(state: AgentState) -> str:
    """Determines whether to continue the loop (call tools) or end."""
    last_message = state['messages'][-1]
    # If the last message is an AIMessage with tool calls, route to action
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        print("--- Decision: Route to Action (Tool Call Detected) ---")
        return "continue"
    # Otherwise, end the graph
    else:
        print("--- Decision: End (No Tool Call) ---")
        return "end"

# Build the Graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("agent", call_model)
workflow.add_node("action", tool_node) # Use ToolNode for actions

# Set entry point
workflow.set_entry_point("agent")

# Add conditional edges from agent
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "action", # If tool call needed, go to action
        "end": END,           # Otherwise, finish
    },
)

# Add edge from action back to agent
# After executing tools, the ToolNode adds ToolMessages to the state.
# We always want the agent to process the tool results.
workflow.add_edge("action", "agent")

# Compile the graph
# Use checkpointer=None for now if not setting up persistence here
compiled_graph = workflow.compile(checkpointer=None)

# You might want to add error handling wrappers around nodes or edges later