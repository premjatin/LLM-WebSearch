import operator
from typing import TypedDict, Annotated, Sequence
import re,json
from typing import Optional, Tuple, Dict, Any
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import xml.etree.ElementTree as ET
from langchain_core.messages import AIMessage, ToolMessage # Need ToolMessage later
from langchain_core.agents import AgentAction, AgentFinish # Need these for structured output
from app.agent.tools import agent_tools # Import the combined list of tools
from app.core.config import settings
from langchain_groq import ChatGroq

# Initialize LLM
llm = ChatGroq(
    groq_api_key=settings.groq_api_key,
    model_name="meta-llama/llama-4-scout-17b-16e-instruct", # Or your preferred model
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
    """
    Invokes the LLM, parses potential XML tool calls, and decides next step.
    """
    print(f"--- Calling LLM ---")
    messages = state['messages']
    response: AIMessage = llm_with_tools.invoke(messages) # Still invoke with bound tools

    print(f"--- Raw LLM Response Object ---")
    print(response) # Keep for debugging
    print(f"--- End Raw Response ---")

    # Attempt to parse XML tool call from content
    parsed_tool_info =  parse_tool_call_from_content(response.content)

    if parsed_tool_info:
        tool_name, tool_input = parsed_tool_info
        print(f"--- Parsed XML Tool Call: Name='{tool_name}', Input={tool_input} ---")

        # Instead of just returning the message, we create an AgentAction
        # This action needs to be stored in the state so the ToolNode can find it.
        # We need to adjust the state and ToolNode interaction.

        # *** Simplification for now: Let's bypass standard ToolNode routing ***
        # *** We will call the tool DIRECTLY based on parsed info ***
        # *** This requires modifying the graph structure significantly ***

        # === Let's try a different approach: Modify the AIMessage ===
        # Attempt to manually add the tool_calls attribute based on parsing
        # Note: This might feel hacky but could work with minimal graph changes

        from langchain_core.utils.function_calling import convert_to_openai_tool
        import uuid

        # Find the tool schema (assuming agent_tools is accessible here)
        tool_schema = None
        for t in agent_tools:
             if t.name == tool_name:
                 # Convert Langchain Tool to the format expected by AIMessage.tool_calls
                 # This format often mimics OpenAI's tool structure
                 tool_schema = convert_to_openai_tool(t)
                 break

        if tool_schema:
             tool_call_id = f"call_{uuid.uuid4()}"
             response.tool_calls = [
                 {
                     "id": tool_call_id,
                     "name": tool_name,
                     "args": tool_input,
                 }
             ]
             # Clear the raw XML content if desired, or keep it? Let's clear it for cleaner logs.
             # response.content = f"(Tool call detected: {tool_name})"
             print(f"--- Manually Added tool_calls to AIMessage: {response.tool_calls} ---")
        else:
             print(f"--- Warning: Could not find schema for parsed tool name '{tool_name}' ---")
             # If schema not found, treat as normal message and don't add tool_calls
             response.tool_calls = [] # Ensure it's empty

    else:
        # No valid XML tool call found in content
         print("--- No XML Tool Call found in content ---")
         # Ensure tool_calls is empty if not explicitly set
         if not hasattr(response, 'tool_calls'):
              response.tool_calls = []
         elif response.tool_calls is None: # Handle case where it might be None
              response.tool_calls = []


    # Always return the (potentially modified) response message
    return {"messages": [response]}
# 2. Action Node: Executes tools
# Use the prebuilt ToolNode which handles executing tools based on AIMessage.tool_calls
tool_node = ToolNode(agent_tools)

def parse_tool_call_from_content(ai_message_content: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    """
    Parses potential tool call strings (XML-like or function-like) from LLM content.
    Handles formats like:
    - '<ToolName>{"arg": "value"}</ToolName>'
    - '<function=ToolName{"arg": "value"} </function>'
    Returns (tool_name, tool_input_dict) or None if no valid call found.
    """
    content = ai_message_content.strip()

    # Pattern 1: XML style (<ToolName>...</ToolName>)
    xml_match = re.match(r"<(\w+)>(.*?)</\1>", content, re.DOTALL)
    if xml_match:
        tool_name = xml_match.group(1)
        argument_str = xml_match.group(2).strip()
        print(f"Parser: Matched XML style for tool '{tool_name}'")
        try:
            tool_input_dict = json.loads(argument_str)
            if not isinstance(tool_input_dict, dict): return None
            return tool_name, tool_input_dict
        except json.JSONDecodeError:
            print(f"Parser Warning: Failed to parse XML content as JSON: {argument_str}")
            return None # Expecting JSON args

    # Pattern 2: Function style (<function=ToolName{...} </function>)
    func_match = re.match(r"<function=(\w+)\s*({.*?})\s*</function>", content, re.DOTALL)
    if func_match:
        tool_name = func_match.group(1)
        argument_str = func_match.group(2).strip()
        print(f"Parser: Matched function style for tool '{tool_name}'")
        try:
            tool_input_dict = json.loads(argument_str)
            if not isinstance(tool_input_dict, dict): return None
            return tool_name, tool_input_dict
        except json.JSONDecodeError:
            print(f"Parser Warning: Failed to parse function content as JSON: {argument_str}")
            return None # Expecting JSON args

    print(f"Parser: No known tool call pattern matched in content: '{content[:100]}...'")
    return None # No known pattern matched
# Define Conditional Edge Logic
def should_continue(state: AgentState) -> str:
    """Determines whether to continue (tool calls present) or end."""
    last_message = state['messages'][-1]
    # Check the potentially manually added tool_calls attribute
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        print("--- Decision: Route to Action (Tool Call Detected in AIMessage) ---")
        return "continue"
    else:
        print("--- Decision: End (No Tool Call Detected in AIMessage) ---")
        return "end"

# --- Build the Graph (No change needed here) ---
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("action", tool_node)
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue, {"continue": "action", "end": END})
workflow.add_edge("action", "agent")

# Compile the graph
# Use checkpointer=None for now if not setting up persistence here
compiled_graph = workflow.compile(checkpointer=None)

# You might want to add error handling wrappers around nodes or edges later