from sqlalchemy.orm import Session
from app.db import crud
from app.agent.graph import compiled_graph, AgentState # Import compiled graph and state
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from typing import List, Dict, Any

async def run_agent(input_message: str, conversation_id: int, db: Session) -> str:
    """
    Runs the LangGraph agent for a given message and conversation.
    Manages history and invokes the compiled graph.
    """
    print(f"--- Running Agent for Conversation ID: {conversation_id} ---")
    print(f"Input Message: {input_message}")

    # 1. Get conversation history
    history: List[BaseMessage] = crud.get_messages_for_conversation(db, conversation_id)
    print(f"Retrieved {len(history)} messages from history.")

    # 2. Format input for the graph
    current_human_message = HumanMessage(content=input_message)
    graph_input_messages = history + [current_human_message]

    # 3. Prepare the initial state for the graph
    initial_state: AgentState = {"messages": graph_input_messages}

    # 4. Define runtime configuration (e.g., recursion limit)
    config = {"recursion_limit": 15}

    # 5. Invoke the graph asynchronously
    # Use ainvoke for async compatibility with FastAPI
    print("--- Invoking LangGraph ---")
    final_state: AgentState = await compiled_graph.ainvoke(initial_state, config=config)
    print("--- LangGraph Invocation Complete ---")

    # 6. Extract the final AI response
    ai_response_message: BaseMessage = final_state['messages'][-1]

    if isinstance(ai_response_message, AIMessage):
        ai_response_text = ai_response_message.content
        print(f"Final AI Response: {ai_response_text[:150]}...")
    else:
        print(f"Warning: Last message was not AIMessage: {type(ai_response_message)}")
        # Fallback: try finding the last AI message in the sequence
        ai_response_text = "Error: Could not determine AI response."
        for msg in reversed(final_state['messages']):
             if isinstance(msg, AIMessage):
                 ai_response_text = msg.content
                 break

    # 7. Save the user message and the AI response to the database
    crud.add_message(db, conversation_id, sender='user', text=input_message)
    crud.add_message(db, conversation_id, sender='ai', text=ai_response_text)
    print("--- User and AI messages saved to DB ---")

    return ai_response_text