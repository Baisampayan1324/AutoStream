# AutoStream Demo Script

Use these questions in your 2-3 minute demo video to showcase the agent's reasoning, memory, and tool-calling capabilities.

---

### Phase 1: Knowledge Retrieval (RAG)
*   **User Question**: `Welcome! What pricing plans does AutoStream offer?`
*   **Goal**: Show the agent fetching data from the internal knowledge base.
*   **User Question**: `What is the video resolution for the Basic plan?`
*   **Goal**: Show the agent's ability to answer specific technical details.

### Phase 2: Intent Detection & Context Switching
*   **User Question**: `This sounds perfect for my content. I want to sign up!`
*   **Goal**: Demonstrate the switch from "Inquiry" mode to "Lead Collection" mode.
*   **User Question**: `Wait, before that, what is your refund policy?`
*   **Goal**: **Showcase Reasoning.** The agent will pause the signup flow, answer the question, and wait for you to continue.

### Phase 3: Multi-Turn State Management
*   **User Question**: `My name is Sam.`
*   **Goal**: Show the terminal capturing data points individually.
*   **User Question**: `My email is sam@example.com.`
*   **Goal**: Show state persistence across messages.

### Phase 4: Final Tool Execution
*   **User Question**: `I create content for YouTube.`
*   **Goal**: **The Big Finish.** All three fields are now full. The agent will trigger the `mock_lead_capture` tool.

---

### Terminal Logs to Highlight
When these appear in your terminal, point them out as proof of "Agentic Behavior":
1. `[SYSTEM] INTENT CLASSIFIED: HIGH_INTENT`
2. `[SYSTEM] DATA CAPTURED: Name=Sam`
3. `[SYSTEM] ACTION TRIGGERED: Lead Capture`
