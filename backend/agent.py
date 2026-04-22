import os
import operator
from typing import Annotated, List, TypedDict, Literal

from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode

from rag import get_knowledge_base_context
from tools import mock_lead_capture


def get_message_content(msg) -> str:
    """Safely extract text content from any message format."""
    if hasattr(msg, "content"):
        return msg.content
    if isinstance(msg, tuple) and len(msg) > 1:
        return msg[1]
    return str(msg)

# Define Agent State
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    intent: str
    collected_name: str
    collected_email: str
    collected_platform: str
    lead_captured: bool

# --- CONFIGURATION ---
MODEL_GROQ_CLASSIFIER = "llama-3.3-70b-versatile"
MODEL_OPENROUTER_EXTRACTOR = "anthropic/claude-3-haiku"
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# Initialize LLMs
groq_llm = ChatGroq(
    model=MODEL_GROQ_CLASSIFIER,
    temperature=0
)

openrouter_llm = ChatOpenAI(
    model=MODEL_OPENROUTER_EXTRACTOR,
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base=OPENROUTER_BASE_URL,
    temperature=0
)

# --- NODES ---

def classify_intent_node(state: AgentState):
    """Classifies user intent every turn with context awareness."""
    last_message = get_message_content(state["messages"][-1])
    
    # Context Check: If we've already started collecting info, stay in high_intent mode
    # unless the user is clearly asking a new question.
    is_collecting = state.get("collected_name") or state.get("collected_email") or state.get("collected_platform")
    is_high_intent_started = state.get("intent") == "high_intent"

    system_prompt = (
        "Classify the user message into exactly one of these: 'greeting', 'inquiry', 'high_intent'.\n"
        "- 'greeting': hello, hi, how are you.\n"
        "- 'inquiry': specific questions about price, refund, support, pro, basic, resolution.\n"
        "- 'high_intent': providing information (names, emails, platforms) or expressing interest in getting started.\n"
        "Note: Short answers like names or email addresses are ALWAYS 'high_intent'.\n"
        "Reply with ONLY the classification word."
    )
    
    response = groq_llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": last_message}
    ])
    
    intent = response.content.strip().lower()
    
    # Override logic: If we are in the middle of collection and it's not a clear inquiry, keep it as high_intent
    if (is_collecting or is_high_intent_started) and "inquiry" not in intent and "greeting" not in intent:
        intent = "high_intent"
    
    # Sanitize
    if "greeting" in intent: intent = "greeting"
    elif "inquiry" in intent: intent = "inquiry"
    else: intent = "high_intent"
    
    print(f"[SYSTEM] INTENT CLASSIFIED: {intent.upper()}")
    return {"intent": intent}

def greeting_node(state: AgentState):
    """Responds to greetings with a formal professional tone."""
    return {
        "messages": [AIMessage(content="Welcome to AutoStream. I am your automated assistant. How may I assist you with our video automation tools today?")]
    }

def rag_node(state: AgentState):
    """Retrieves info using LLM-powered context awareness."""
    kb_context = get_knowledge_base_context()
    
    # We pass the messages to the LLM so it knows the conversation context
    # (e.g., if the user says "how about pro", it knows we are talking about refunds)
    system_prompt = (
        "You are the AutoStream Assistant. Use the following Knowledge Base to answer the user's question.\n"
        "If the user's question is vague (e.g. 'how about pro?'), use the conversation history to understand the context.\n"
        "Knowledge Base:\n"
        f"{kb_context}\n\n"
        "Answer concisely and professionally."
    )
    
    # Use Groq for fast, intelligent RAG response
    response = groq_llm.invoke([
        {"role": "system", "content": system_prompt},
        *state["messages"] # This passes the entire history!
    ])
    
    print(f"[SYSTEM] RAG RETRIEVAL: Answered based on knowledge base context.")
    return {
        "messages": [AIMessage(content=response.content)]
    }

def lead_collection_node(state: AgentState):
    """Extracts information and asks for missing fields."""
    last_message = get_message_content(state["messages"][-1])
    
    # 1. Extraction Logic (using OpenRouter)
    extraction_prompt = (
        f"Extract information from this message: '{last_message}'.\n"
        "Return a JSON-like string with 'name', 'email', 'platform'.\n"
        "If a field is not found, leave it as null.\n"
        "Example: {'name': 'John', 'email': null, 'platform': 'YouTube'}"
    )
    
    extraction = openrouter_llm.invoke(extraction_prompt).content
    
    # 2. Robust JSON Extraction
    import re
    import json
    
    # Extract JSON content from within curly braces (handles markdown or extra text)
    match = re.search(r'\{.*\}', extraction, re.DOTALL)
    if match:
        try:
            # Clean common LLM formatting issues
            json_str = match.group(0).replace("'", "\"")
            extracted_data = json.loads(json_str)
        except:
            extracted_data = {"name": None, "email": None, "platform": None}
    else:
        extracted_data = {"name": None, "email": None, "platform": None}

    # Update state with extracted fields if they are not already filled
    new_data = {}
    if extracted_data.get("name") and not state.get("collected_name"):
        new_data["collected_name"] = extracted_data["name"]
        print(f"[SYSTEM] DATA CAPTURED: Name={extracted_data['name']}")
        
    if extracted_data.get("email") and not state.get("collected_email"):
        new_data["collected_email"] = extracted_data["email"]
        print(f"[SYSTEM] DATA CAPTURED: Email={extracted_data['email']}")
        
    if extracted_data.get("platform") and not state.get("collected_platform"):
        new_data["collected_platform"] = extracted_data["platform"]
        print(f"[SYSTEM] DATA CAPTURED: Platform={extracted_data['platform']}")

    # Merge current data for logic
    name = new_data.get("collected_name") or state.get("collected_name")
    email = new_data.get("collected_email") or state.get("collected_email")
    platform = new_data.get("collected_platform") or state.get("collected_platform")

    # 2. Response Logic
    if not name:
        response = "I'd love to help you get started! To get you set up, what is your name?"
    elif not email:
        response = f"Nice to meet you, {name}! What is your best email address for us to reach out?"
    elif not platform:
        response = "Great! And which platform are you primarily focused on (e.g., YouTube, Instagram, TikTok)?"
    else:
        response = f"Got it! I have everything I need: {name}, {email}, on {platform}. Processing your request..."

    return {
        **new_data,
        "messages": [AIMessage(content=response)]
    }

def lead_capture_node(state: AgentState):
    """Triggers the lead capture tool."""
    name = state["collected_name"]
    email = state["collected_email"]
    platform = state["collected_platform"]
    
    result = mock_lead_capture.invoke({"name": name, "email": email, "platform": platform})
    
    return {
        "messages": [AIMessage(content=result)],
        "lead_captured": True
    }

# --- EDGES / ROUTING ---

def route_after_classification(state: AgentState):
    return state["intent"]

def route_after_collection(state: AgentState):
    # Check if all fields are filled
    if state.get("collected_name") and state.get("collected_email") and state.get("collected_platform"):
        return "capture"
    return "end"

# Build Graph
builder = StateGraph(AgentState)

builder.add_node("classify", classify_intent_node)
builder.add_node("greeting", greeting_node)
builder.add_node("rag", rag_node)
builder.add_node("collection", lead_collection_node)
builder.add_node("capture", lead_capture_node)

builder.add_edge(START, "classify")

builder.add_conditional_edges(
    "classify",
    route_after_classification,
    {
        "greeting": "greeting",
        "inquiry": "rag",
        "high_intent": "collection"
    }
)

builder.add_conditional_edges(
    "collection",
    route_after_collection,
    {
        "capture": "capture",
        "end": END
    }
)

builder.add_edge("greeting", END)
builder.add_edge("rag", END)
builder.add_edge("capture", END)

# Compile
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)
