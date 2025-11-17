# 🎙️ ***`Voice Screening Agent`***


#### Overview
The **Voice Screening Agent** conducts automated phone interviews and integrates with the **LangGraph HR Orchestrator**.  
It uses **Twilio** for phone calls, **Whisper/ASR** for speech-to-text, **ElevenLabs** for natural voice output, and **LangGraph** for dialogue logic.

---

#### Tools
| Component | Purpose |
|------------|----------|
| **Twilio** | Initiates and streams live phone calls |
| **Whisper / ASR** | Converts candidate speech → text |
| **LangGraph Voice Agent** | Manages interview flow & logic |
| **ElevenLabs TTS (Streaming)** | Converts text → realistic spoken audio |
| **HR Orchestrator** | Triggers the voice interview and collects results |

***links:***
- https://elevenlabs.io/docs/agents-platform/phone-numbers/twilio-integration/native-integration#making-outbound-calls
- https://www.twilio.com/docs/voice/twiml/stream
- https://elevenlabs.io/docs/agents-platform/libraries/python
---

#### Flow
```text
Candidate ↔ Twilio (Call Audio)
↓
Whisper / ASR (Speech→Text)
↓
LangGraph Voice Agent (decide next prompt)
↓
ElevenLabs TTS (Text→Speech)
↓
Twilio (Play audio to candidate)
↓
[Post-Call Analysis]
   ├─ Transcript + call metadata
   └─ LLM Judge → Tone, confidence, coherence, summary
```

#### Interface
- **Outbound call**: triggered via `/start_call` endpoint → connects candidate to the agent  
- **Real-time audio**: exchanged over `/voice_stream` WebSocket (Twilio <-> Agent)  
- **Status updates**: handled through `/callback` (call started, ended, failed) 
- **Post-call evaluation**: triggered automatically after call completion via `/analyze_call`

#### Voice Screening Entry Options Comparison
| **Aspect**             | **Phone Number (Recommended)**                    | **Web Interface (Optional)**                 |
| ---------------------- | ------------------------------------------------- | -------------------------------------------- |
| **Start method**       | Candidate calls a Twilio number                   | Candidate clicks “Start Voice Screening”     |
| **UI needed**          | ❌ None                                            | ✅ Yes (web app with Twilio WebRTC)           |
| **Tech stack**         | Twilio Voice + ASR + ElevenLabs + LangGraph       | Twilio WebRTC + ASR + ElevenLabs + LangGraph |
| **Call trigger**       | Inbound Twilio webhook (`/voice_screening_entry`) | Web call via backend endpoint                |
| **Audio flow**         | Phone ↔ Twilio ↔ Backend                          | Browser ↔ Twilio ↔ Backend                   |
| **Post-call analysis** | LLM Judge evaluates tone & coherence              | Same                                         |
| **HR role**            | Reviews results only                              | Reviews results only                         |
| **Pros**               | Simple, fast, scalable                            | Branded, browser-based                       |
| **Cons**               | No visuals                                        | More dev effort                              |
| **Best for**           | MVP / production rollout                          | Custom candidate UX                          |


#### Result
The agent returns:
- Candidate's transcribed responses
- Post-call analysis:
  - Conversational tone & confidence
  - Coherence, politeness, and engagement
- Screening summary (key traits, tone, readiness)
- Pass/fail or next-step recommendation