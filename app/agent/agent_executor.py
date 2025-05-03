from sqlalchemy.orm import Session
from app.db import crud
from app.agent.graph import compiled_graph, AgentState # Import compiled graph and state
# Add SystemMessage import
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from typing import List, Dict, Any

async def run_agent(input_message: str, conversation_id: int, user_id: int, db: Session) -> str:
    """
    Runs the LangGraph agent for a given message and conversation.
    Manages history and invokes the compiled graph.
    """
    print(f"--- Running Agent for User ID: {user_id}, Conversation ID: {conversation_id} ---")
    print(f"Input Message: {input_message}")

    # 1. Get conversation history
    history: List[BaseMessage] = crud.get_messages_for_conversation(
        db=db,
        user_id=user_id, # Pass the user ID
        conversation_id=conversation_id # Pass the conversation ID
    )
    print(f"Retrieved {len(history)} messages from history.")

    # === ADD/DEFINE SYSTEM PROMPT ===
    system_prompt_content = (
        "You are a helpful and conversational AI assistant. Your primary goal is to provide accurate and relevant information.\n\n"
        "**Conversational Interaction:**\n"
        "- Answer simple greetings (hello, how are you), expressions of gratitude (thank you), and direct questions about your AI nature conversationally *without* using tools.\n\n"
        "**Tool Usage Guidelines:**\n"
        "- **InternalKnowledgeSearch:** Use this tool FIRST if the user's query seems to relate specifically to internal documents, procedures, or data explicitly provided to you.\n"
        "- **WebSearch:** Use this tool when the user asks for:\n"
        "    - Specific, factual information about recent events (e.g., news, sports results, recent developments).\n"
        "    - Real-time information (e.g., stock prices - though acknowledge limitations, weather).\n"
        "    - Information about entities or topics likely not in your training data or the internal knowledge base.\n"
        "- **Crucially:** If you realize you lack the necessary up-to-date or specific information to answer a factual question accurately based on your internal knowledge, **use the WebSearch tool to find the answer** instead of stating you don't have access.\n\n"
        "**Important Execution Note:** When you determine a tool is needed based on the guidelines, invoke the correct tool function with the necessary arguments. Your response structure should facilitate this tool invocation.\n\n" 
        "**Context and Queries:**\n"
        "- Always pay close attention to the entire conversation history to understand context and resolve pronouns (he, she, it, they).\n"
        "- When using a tool, formulate a specific search query based on the entities and details discussed in the conversation (e.g., for 'when did he score last?' after discussing Messi, search 'Lionel Messi last goal date')."
    )
    system_message = SystemMessage(content=system_prompt_content)

    # 2. Format input for the graph (PREPEND System Prompt)
    current_human_message = HumanMessage(content=input_message)
    # Ensure system prompt is always the very first message
    graph_input_messages = [system_message] + history + [current_human_message]

    # === Add logging to verify messages ===
    print("--- Messages being sent to graph: ---")
    for i, msg in enumerate(graph_input_messages):
        print(f"  {i}: [{msg.type}] {str(msg.content)[:100]}...")
    # === End logging ===


    # 3. Prepare the initial state for the graph
    initial_state: AgentState = {"messages": graph_input_messages}

    # 4. Define runtime configuration (e.g., recursion limit)
    config = {"recursion_limit": 15}

    # 5. Invoke the graph asynchronously
    print("--- Invoking LangGraph ---")
    final_state: AgentState = await compiled_graph.ainvoke(initial_state, config=config)
    print("--- LangGraph Invocation Complete ---")

    # 6. Extract the final AI response (logic remains the same)
    ai_response_message: BaseMessage = final_state['messages'][-1]

    if isinstance(ai_response_message, AIMessage):
        ai_response_text = ai_response_message.content
        print(f"Final AI Response: {ai_response_text[:150]}...")
    else:
        # ... (fallback logic) ...
        print(f"Warning: Last message was not AIMessage: {type(ai_response_message)}")
        ai_response_text = "Error: Could not determine AI response."
        for msg in reversed(final_state['messages']):
             if isinstance(msg, AIMessage):
                 if not (hasattr(msg, 'tool_calls') and msg.tool_calls):
                    ai_response_text = msg.content
                    break
        if ai_response_text.startswith("Error:"):
             ai_response_text = "I encountered an issue processing the final response."

    # 7. Save the user message and the AI response to the database
    # Make sure not to save the initial system prompt to the DB history
    crud.add_message(db, conversation_id, sender='user', text=input_message)
    crud.add_message(db, conversation_id, sender='ai', text=ai_response_text)
    print("--- User and AI messages saved to DB ---")

    return ai_response_text