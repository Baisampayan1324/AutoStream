from langchain.tools import tool

@tool
def mock_lead_capture(name: str, email: str, platform: str) -> str:
    """Simulates capturing a lead into a CRM database."""
    print(f"\n[SYSTEM] ACTION TRIGGERED: Lead Capture")
    print(f"[SYSTEM] DATA: Name={name}, Email={email}, Platform={platform}")
    print(f"[SYSTEM] STATUS: Lead successfully recorded in CRM.")
    
    return f"Success! {name}, your interest has been recorded. Our team will reach out to you at {email}."
