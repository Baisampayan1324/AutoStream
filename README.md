# AutoStream AI Lead Capture Agent

This project is a technical prototype developed for the **ServiceHive (Inflx)** ML Intern assignment. It implements a "Social-to-Lead" agentic workflow for **AutoStream**, a fictional video automation SaaS.

## Setup
1. **Clone the repository** and navigate to the directory.
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment**:
   Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=your_groq_key_here
   OPENROUTER_API_KEY=your_openrouter_key_here
   OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
   ```
4. **Run the Dashboard (Recommended)**:
   ```bash
   cd backend
   python app.py
   ```
   *Then open `frontend/index.html` in your browser.*

## Architecture (Technical Deep Dive)
Unlike traditional linear chatbots, this system utilizes **LangGraph** to implement a cyclic state machine. The core architecture revolves around an `AgentState` object that persists across turns using a `MemorySaver` checkpointer. 

The workflow starts with a **Classifier Node** (powered by Groq for sub-second inference) that re-evaluates the user's intent on every message. This prevents the agent from getting "stuck" in a specific loop. If the intent is an inquiry, the system routes to an **AI-Powered RAG Node** that performs contextual retrieval from a local `knowledge_base.json`, ensuring responses are grounded in product truth.

For "High Intent" users, the agent enters a **Lead Collection Node** (powered by OpenRouter for high-reasoning extraction). This node captures 'Name', 'Email', and 'Platform' from the context, prompting for missing fields one-by-one. Only once the state is fully populated does the graph transition to the **Lead Capture Node**, which executes the `mock_lead_capture` tool—a pattern that mirrors real-world CRM integrations.

## WhatsApp Deployment via Webhooks
To deploy this agent to WhatsApp for production use, follow this technical blueprint:

1.  **Meta Cloud API Setup**: Register a Meta Developer account and configure a WhatsApp Business profile. Generate a Permanent Access Token and verify your webhook.
2.  **Webhook Endpoint**: Deploy a Python backend (FastAPI or Flask) with a `POST /webhook` endpoint. This endpoint must handle the Meta challenge (GET) and incoming message payloads (POST).
3.  **Message Processing**:
    *   Extract the `sender_id` (phone number) and the `message_body` from the incoming JSON.
    *   Initialize the LangGraph agent with a `thread_id` mapped to the `sender_id`. This ensures that state (collected name/email) is isolated per user and persists across days.
4.  **Backend Logic**: Call `graph.invoke()` with the user's message. Use a persistent checkpointer (like Redis or PostgreSQL) instead of the in-memory `MemorySaver` to ensure state is not lost on server restarts.
5.  **Response Delivery**: Send the agent's response back to the user via a `POST` request to the Meta Cloud API `/messages` endpoint using the `sender_id`.

## 🛠️ Tech Stack
- **LangGraph**: Orchestration & Cyclic State Management
- **Groq (Llama 3.3)**: Intent Classification (Ultra-low latency inference)
- **OpenRouter (Claude 3 Haiku)**: High-reasoning Information Extraction
- **FastAPI**: Production-grade asynchronous Python API
- **Vanilla HTML5/CSS3/JS**: Premium Light-Themed Lead Dashboard
