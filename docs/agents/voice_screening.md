# Voice Screening MVP

## Overview

The **Voice Screening MVP** provides a simple browser-based voice interview interface using Streamlit and OpenAI Realtime API. This is a simplified implementation that removes the complexity of LangGraph agents, Twilio telephony, and FastAPI servers.

## Architecture

**Simple MVP Architecture:**
- **Streamlit UI**: Web interface with toggle recording button
- **WebSocket Proxy**: FastAPI proxy for browser WebSocket authentication
- **OpenAI Realtime API**: Real-time speech-to-speech via WebSocket
- **Real-time transcription**: Live transcript display
- **Real-time TTS**: Audio playback in browser with sequential queue
- **Simple backend**: Post-session analysis and database storage

## Components

| Component | Purpose |
|------------|----------|
| **Streamlit UI** | Main interface with interview controls and transcript display |
| **HTML/JavaScript Component** | WebSocket connection via proxy, audio recording/playback with queue |
| **WebSocket Proxy** | FastAPI service to handle OpenAI authentication (browsers can't set custom headers) |
| **OpenAI Realtime API** | Handles speech-to-text and text-to-speech in real-time (gpt-4o-mini-realtime-preview) |
| **Analysis Function** | Simple GPT-4 analysis of transcript (no LangGraph) |
| **Database Utilities** | Save results to database |

## Flow

```text
User enters email and requests authentication code
↓
Proxy generates 6-digit code (MVP: displayed directly; production: sent via email/SMS)
↓
User enters email and code to verify
↓
Proxy validates code and returns session token
↓
User clicks "Start Interview"
↓
Browser opens WebSocket to WebSocket Proxy (with session token in query param)
↓
Proxy validates session token
↓
Proxy forwards connection to OpenAI Realtime API with API key authentication
↓
Proxy configures OpenAI session (modalities, instructions, voice, etc.)
↓
Proxy sends greeting request to OpenAI
↓
Agent greets candidate (first TTS response)
↓
User clicks mic button to start recording (toggle on)
↓
Browser streams audio chunks to OpenAI via proxy
↓
OpenAI returns transcriptions + TTS audio in real-time
↓
Audio chunks queued and played sequentially in browser
↓
Transcript shown live in Streamlit UI
↓
User clicks mic button again to stop and send (toggle off)
↓
Audio buffer committed to OpenAI
↓
User clicks "End Interview"
↓
Send transcript to backend for analysis
↓
GPT-4 analyzes transcript (sentiment, confidence, communication)
↓
Results saved to database
```

## Implementation Details

### Streamlit UI (`src/voice_screening_ui/app.py`)

**Features:**
- **Authentication screen**: Email and code input fields
- "Start Interview" button to initialize session
- Toggle microphone button (click to start, click again to stop and send)
- Live transcript display area
- Session controls (end interview, logout)
- Analysis and results display
- Database integration
- Debug panel for connection and audio troubleshooting

**Session State:**
- `session_token`: Authentication token from proxy
- `user_email`: Authenticated user's email
- `session_id`: Unique interview session identifier
- `transcript`: List of transcript entries
- `is_interview_active`: Boolean flag for active session
- `candidate_id`: Candidate UUID

### HTML/JavaScript Component (`src/voice_screening_ui/components/voice_interface.html`)

**Features:**
- WebSocket connection to WebSocket Proxy with session token authentication
- Audio recording via browser ScriptProcessor API (PCM16)
- Audio playback via Web Audio API with sequential queue
- Real-time transcript updates
- Toggle recording (click to start/stop)
- Audio resampling from 24kHz to browser sample rate
- Debug panel for troubleshooting

**Key Functions:**
- `connectWebSocket()`: Establishes connection to WebSocket Proxy (with session token)
- `toggleRecording()`: Toggles recording state (start/stop)
- `startRecording()`: Captures microphone audio and streams to API
- `stopRecording()`: Stops recording and commits audio buffer
- `handleRealtimeMessage()`: Processes responses from OpenAI
- `queueAudioChunk()`: Queues audio chunks for sequential playback
- `processAudioQueue()`: Plays audio chunks one at a time
- `playAudioChunk()`: Decodes and plays individual TTS audio chunks

**Note:** Session configuration and greeting are now handled by the proxy, not the client.

### Analysis Function (`src/voice_screening_ui/analysis.py`)

**Simple function** (no LangGraph):
- Receives transcript text
- Uses OpenAI GPT-4 with structured output
- Returns `VoiceScreeningOutput` with scores and summary
- No agent nodes or graph execution

### Database Integration (`src/voice_screening_ui/utils/db.py`)

**Function:**
- `write_voice_results_to_db()`: Saves results to database
- Updates candidate status to `voice_done`
- Uses existing `VoiceScreeningResult` model

### WebSocket Proxy (`src/voice_screening_ui/proxy.py`)

**Features:**
- **Authentication endpoints**: `/auth/login` and `/auth/verify`
- **Session management**: In-memory token storage (MVP; use Redis/DB in production)
- **WebSocket proxy**: `/ws/realtime` endpoint with session token validation
- **Session configuration**: Handles OpenAI session setup server-side
- **Greeting**: Automatically sends greeting after session configuration
- **Health check**: `/health` endpoint for monitoring

**Authentication Flow:**
1. User requests code via `POST /auth/login` with email
2. Proxy generates 6-digit code (MVP: returns directly; production: send via email/SMS)
3. User verifies via `POST /auth/verify` with email and code
4. Proxy validates and returns session token (valid for 1 hour)
5. WebSocket connection requires `token` query parameter

**Session Configuration:**
- Moved from frontend to proxy for better security and control
- Configured automatically when WebSocket connects
- Includes modalities, instructions, voice, audio format, turn detection

## Environment Variables

```bash
OPENAI_API_KEY=your_openai_api_key  # Required for Realtime API (stored in proxy only)
```

**Security:**
- API key stored in proxy environment variables (never exposed to browser)
- User authentication via email/code before WebSocket access
- Session tokens expire after 1 hour
- Auth codes expire after 10 minutes
- Proxy handles all OpenAI authentication server-side

## Usage

### Running the Application

```bash
# Using Streamlit directly
streamlit run src/voice_screening_ui/app.py

# Or via Docker (Streamlit service)
docker compose up voice_screening
```

#### troubleshootips tips

- if you see a warning on env variable not being set, pass the .env manually and rebuild on down (subsequent build will be faste due to docker layer caching)
``` bash
cd docker
docker-compose --env-file "../.env" up voice_screening -d --build
```

- run streamlit with python path set
``` bash
PYTHONPATH=. streamlit run src/voice_screening_ui/app.py
```

### User Flow

1. Start WebSocket proxy: `docker compose up websocket_proxy` (or run `python src/voice_screening_ui/proxy.py`)
2. Open Streamlit UI at `http://localhost:8502` (or configured port)
3. **Authentication:**
   - Enter your email address
   - Click "Request Code" to get authentication code
   - Enter the code and click "Verify & Login"
4. Enter candidate email (optional for MVP)
5. Click "Start Interview"
6. Browser requests microphone permission
7. WebSocket connects to proxy with session token (proxy connects to OpenAI Realtime API)
8. Proxy configures session and sends greeting
9. Agent greets candidate
10. User clicks mic button to start recording
11. User speaks, audio streams to OpenAI
12. Transcript appears in real-time
13. Agent responds with audio (played sequentially)
14. User clicks mic button again to stop and send
15. User clicks "End Interview"
16. Click "Analyze Interview" to get results
17. Optionally save results to database
18. Click "Logout" to end session

## Technical Details

### OpenAI Realtime API

**WebSocket Connection:**
- Model: `gpt-realtime-mini`
- URL: `wss://api.openai.com/v1/realtime?model=gpt-realtime-mini`
- Headers: `Authorization: Bearer {API_KEY}`, `OpenAI-Beta: realtime=v1`
- Format: PCM16 audio at 24kHz, JSON messages
- Turn Detection: Server-side VAD with 10s silence duration (prevents auto-commit during recording)

**Key Message Types:**
- `session.update`: Configure session (modalities, voice, instructions)
- `input_audio_buffer.append`: Send audio chunks
- `input_audio_buffer.commit`: Commit audio for processing
- `response.audio_transcript.done`: Receive transcriptions
- `response.audio.delta`: Receive TTS audio chunks
- `response.text.done`: Receive text responses

### Audio Processing

**Recording:**
- Uses browser `ScriptProcessor` API (deprecated but functional)
- Captures audio at browser sample rate (typically 44.1kHz or 48kHz)
- Converts to PCM16 format
- Encodes to base64 for WebSocket transmission
- Streams chunks via `input_audio_buffer.append`
- Commits buffer via `input_audio_buffer.commit` when recording stops

**Playback:**
- Receives base64 PCM16 audio at 24kHz
- Decodes using `DataView` for proper byte order (little-endian)
- Converts PCM16 to Float32Array
- Resamples from 24kHz to browser sample rate using `OfflineAudioContext`
- Queues chunks for sequential playback (prevents overlapping audio)
- Plays through browser audio context

## Simplifications from Original Design

**Removed:**
- LangGraph agent complexity
- Twilio telephony integration
- FastAPI server
- Media Streams handling
- Complex state management
- Supervisor agent integration

**Kept:**
- Database models and utilities
- Analysis logic (simplified)
- Streamlit UI pattern
- OpenAI Realtime API integration

## File Structure

```
src/voice_screening_ui/
├── app.py                    # Main Streamlit UI (with authentication screen)
├── proxy.py                  # WebSocket proxy with auth endpoints and session management
├── analysis.py               # Simple analysis function
├── components/
│   ├── voice_interface.html  # HTML/JS for WebSocket and audio (no API key handling)
│   └── __init__.py
└── utils/
    ├── db.py                 # Database utilities
    └── __init__.py
```

## Testing

**Manual Testing:**
1. Start Streamlit app (tested and works)
2. Test WebSocket connection (tested and works)
3. Test microphone access (tested and works)
4. Test audio recording and playback (tested and works)
5. Test transcript display (not tested)
6. Test analysis function (doesn't work, need work, a lot of work)
7. Test database saving (doesn't work, need work, a lot, a lot of work)

### Verification Script
To verify the integration of the voice screener with the candidate database and static questions, you can run the provided verification script.

**Option 1: Run via Docker (Recommended)**
This uses the containerized environment which already has all dependencies and network access to the database.
```bash
docker compose -f docker/docker-compose.yml run --rm -e POSTGRES_HOST=db websocket_proxy python tests/verify_voice_integration.py
```

**Option 2: Run Locally**
If you prefer to run it locally, you need to install the database requirements first:
```bash
pip install -r requirements/db.txt
python tests/verify_voice_integration.py
```

**Known Limitations:**
- Uses deprecated `ScriptProcessor` API (should migrate to `AudioWorklet`)
- Authentication codes displayed directly in MVP (should be sent via email/SMS in production)
- Session tokens stored in-memory (should use Redis/database in production)
- Simple error handling
- Limited session management
- Audio resampling may introduce slight latency

## Future Enhancements

- Migrate from `ScriptProcessor` to `AudioWorklet` API
- Send authentication codes via email/SMS (instead of displaying directly)
- Use Redis or database for session token storage (instead of in-memory)
- Add session persistence across page refreshes
- Improve error handling and reconnection logic
- Add recording playback
- Add interview question templates
- Optimize audio resampling performance
- Add audio level visualization
- Add rate limiting for authentication endpoints
- Add session refresh mechanism
- Integrate with supervisor agent (if needed)
