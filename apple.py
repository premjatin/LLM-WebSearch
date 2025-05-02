import requests
import json

BASE_URL = "http://localhost:8000"
conversation_id = None # Start with no conversation ID

while True:
    user_input = input("You: ")
    if user_input.lower() in ["quit", "exit"]:
        break

    payload = {
        "user_message": user_input,
        "conversation_id": conversation_id # Send current ID (None for first message)
    }

    try:
        response = requests.post(f"{BASE_URL}/chat", json=payload)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        data = response.json()
        print(f"AI: {data['ai_response']}")

        # IMPORTANT: Update conversation_id for the next turn
        conversation_id = data['conversation_id']

    except requests.exceptions.RequestException as e:
        print(f"Error contacting API: {e}")
    except json.JSONDecodeError:
        print(f"Error decoding server response: {response.text}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

print("Chat ended.")