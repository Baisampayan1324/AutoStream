import os
import uuid
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Check for API keys
if not os.getenv("GROQ_API_KEY") or not os.getenv("OPENROUTER_API_KEY"):
    print("WARNING: API keys missing in .env. Please check GROQ_API_KEY and OPENROUTER_API_KEY.")

from agent import graph

def run_agent():
    print("="*50)
    print("AutoStream Conversational AI Agent (Inflx Prototype)")
    print("Agent ready. Type 'exit' or 'quit' to stop.")
    print("="*50)

    # thread_id used for persistent memory across the session
    config = {"configurable": {"thread_id": "user_session_1"}}

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() in ["exit", "quit", "bye"]:
            print("AutoStream Agent: Goodbye! Have a great day editing your videos!")
            break

        if not user_input:
            continue

        # Stream the graph execution
        # We use stream to show the flow, but we'll print the final message to the user
        events = graph.stream(
            {"messages": [("user", user_input)]},
            config,
            stream_mode="values"
        )

        for event in events:
            if "messages" in event:
                last_msg = event["messages"][-1]
                # Handle both Message objects and tuples ("user", "content")
                if hasattr(last_msg, "type") and last_msg.type == "ai":
                    # Latest message is already in state, we'll print at the end
                    pass
        
        # After stream finishes, print the final AI message from the state
        final_state = graph.get_state(config)
        final_messages = final_state.values.get("messages", [])
        
        if final_messages and final_messages[-1].type == "ai":
            print(f"\nAutoStream: {final_messages[-1].content}")

if __name__ == "__main__":
    run_agent()
