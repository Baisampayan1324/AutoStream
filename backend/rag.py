import json
import os

def get_knowledge_base_context() -> str:
    """Returns the entire knowledge base as a formatted string for the LLM."""
    kb_path = os.path.join(os.path.dirname(__file__), "knowledge_base.json")
    with open(kb_path, "r") as f:
        kb = json.load(f)
    
    return json.dumps(kb, indent=2)
