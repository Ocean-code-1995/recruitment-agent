# 🎙️ ***`Voice Screening Agent`***


#### Overview
The **Voice Screening Agent** conducts automated phone interviews and integrates with the **LangGraph HR Orchestrator**.  
It uses a **hybrid architecture** combining:
- **FastAPI server**: Handles Twilio webhooks and real-time audio streaming
- **LangGraph agent**: Manages conversation logic and post-call analysis
- **Twilio**: Initiates and streams live phone calls
- **OpenAI Realtime API**: Handles speech-to-text transcription
- **Twilio TTS**: Converts agent responses to speech using native `<Say>` instructions

---

#### Architecture Components
| Component | Purpose |
|------------|----------|
| **Twilio** | Initiates outbound calls and streams live audio via Media Streams |
| **OpenAI Realtime API** | Converts candidate speech → text in real-time via WebSocket |
| **LangGraph Voice Agent** | Manages interview flow, question generation, and conversation logic |
| **Twilio TTS (`<Say>`)** | Converts agent text responses → spoken audio |
| **FastAPI Server** | Handles webhooks, media streams, and orchestrates real-time audio flow |
| **HR Orchestrator** | Triggers the voice interview via tool call and collects results |

***links:***
- https://platform.openai.com/docs/guides/realtime
- https://www.twilio.com/docs/voice/twiml/stream
- https://www.twilio.com/docs/voice/twiml/say
- https://docs.langchain.com/oss/python/langgraph/overview

---

#### Flow
```text
Supervisor Agent → start_voice_screening_tool(candidate_id, phone_number)
↓
Voice Agent → initiate_outbound_call() via Twilio API
↓
Twilio → Calls candidate's phone number
↓
Twilio → POST /voice/webhook (call status)
↓
FastAPI → Starts Media Stream → POST /voice/media
↓
Audio Flow: Candidate ↔ Twilio Media Stream ↔ FastAPI ↔ OpenAI Realtime API (WebSocket)
↓
OpenAI Realtime API → Returns transcriptions
↓
FastAPI → Calls Voice Agent conversation logic
↓
Voice Agent → Generates next question/prompt
↓
FastAPI → Converts to TwiML <Say> → Twilio speaks to candidate
↓
[Call Ends]
↓
FastAPI → Triggers Voice Agent analyze_call node
↓
Voice Agent → LLM evaluates transcript (sentiment, confidence, communication)
↓
Voice Agent → Updates database with results
↓
Candidate status → Updated to 'voice_done'
```

#### API Endpoints

**FastAPI Server** (`src/voice_screening_ui/server.py`):

- **`POST /voice/webhook`**: Twilio status callbacks
  - Handles call events: `ringing`, `in-progress`, `completed`
  - Generates TwiML responses for call setup
  - Manages Media Stream initiation

- **`POST /voice/media`**: Twilio Media Streams webhook
  - Receives real-time audio chunks from Twilio
  - Forwards audio to OpenAI Realtime API
  - Processes transcriptions and agent responses

- **`POST /voice/start`**: Internal endpoint to initiate calls
  - Called by voice agent to start screening
  - Accepts JSON: `{"candidate_id": "...", "phone_number": "..."}`
  - Returns: `{"call_sid": "...", "status": "initiated"}`

- **`GET /health`**: Health check endpoint

#### LangGraph Agent Structure

**VoiceScreeningAgent** (`src/agents/voice_screening/agent.py`):

- **Extends**: `BaseAgent` (LangGraph-compatible)
- **Graph Nodes**:
  1. `initiate_call`: Starts Twilio outbound call
  2. `handle_conversation`: Manages dialogue flow (called by FastAPI during call)
  3. `analyze_call`: Post-call LLM evaluation
  4. `update_database`: Saves results to database

- **Public Method**: `start_voice_screening(candidate_id, phone_number)` → Returns Call SID

- **Tool**: `start_voice_screening_tool` - Callable by supervisor agents

#### Implementation Details

**Hybrid Architecture**:
- **FastAPI** handles real-time webhooks and audio streaming (the "plumbing")
- **LangGraph Agent** manages high-level conversation logic and orchestration
- Separation of concerns: FastAPI for real-time I/O, LangGraph for reasoning

**Call Initiation**:
- Supervisor agent calls `start_voice_screening_tool(candidate_id, phone_number)`
- Voice agent initiates Twilio outbound call via `initiate_outbound_call()`
- Call runs asynchronously; FastAPI handles real-time events

**Real-Time Processing**:
- Twilio Media Streams send audio chunks to `/voice/media`
- FastAPI forwards audio to OpenAI Realtime API via WebSocket
- OpenAI returns transcriptions in real-time
- FastAPI calls voice agent for conversation decisions
- Agent responses converted to TwiML `<Say>` → Twilio speaks to candidate

**Post-Call Analysis**:
- When call ends, FastAPI triggers agent's `analyze_call` node
- LLM evaluates transcript for sentiment, confidence, communication scores
- Results saved to `VoiceScreeningResult` table
- Candidate status updated to `voice_done`

#### Environment Variables Required

```bash
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890  # E.164 format
OPENAI_API_KEY=your_openai_api_key
VOICE_SCREENING_WEBHOOK_URL=https://your-domain.com  # Public URL for Twilio webhooks
```


#### Result Schema

**VoiceScreeningOutput** (`src/agents/voice_screening/schemas/output_schema.py`):

The agent returns structured results stored in the database:

- **`sentiment_score`** (0-1): Overall positive/negative tone
- **`confidence_score`** (0-1): Candidate's confidence level
- **`communication_score`** (0-1): Clarity, articulation, professionalism
- **`llm_summary`**: LLM-generated summary of the interview
- **`llm_judgment_json`**: Structured judgment data (optional)
- **`key_traits`**: List of identified personality/technical traits
- **`recommendation`**: Pass/fail or next-step recommendation

**Database Storage**:
- Results saved to `voice_screening_results` table
- Full transcript stored in `transcript_text` column
- Call SID tracked for reference
- Candidate status automatically updated to `voice_done`

#### Usage Example

```python
from src.agents.voice_screening.tools import start_voice_screening_tool

# Supervisor agent can call this tool
result = start_voice_screening_tool.invoke({
    "candidate_id": "uuid-here",
    "phone_number": "+1234567890"
})
# Returns: "Voice screening call initiated. Call SID: CAxxxxx"
```

#### Docker Setup

The voice screening API runs as a separate service:

```bash
docker compose up voice_api
```

Service exposed on port `8000` and accessible at `http://localhost:8000`