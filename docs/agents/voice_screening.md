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
User clicks "Start Interview"
↓
Browser opens WebSocket to WebSocket Proxy
↓
Proxy forwards connection to OpenAI Realtime API with authentication
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
- "Start Interview" button to initialize session
- Toggle microphone button (click to start, click again to stop and send)
- Live transcript display area
- Session controls (end interview)
- Analysis and results display
- Database integration
- Debug panel for connection and audio troubleshooting

**Session State:**
- `session_id`: Unique session identifier
- `transcript`: List of transcript entries
- `is_interview_active`: Boolean flag for active session
- `candidate_id`: Candidate UUID

### HTML/JavaScript Component (`src/voice_screening_ui/components/voice_interface.html`)

**Features:**
- WebSocket connection to WebSocket Proxy (which connects to OpenAI)
- Audio recording via browser ScriptProcessor API (PCM16)
- Audio playback via Web Audio API with sequential queue
- Real-time transcript updates
- Toggle recording (click to start/stop)
- Audio resampling from 24kHz to browser sample rate
- Debug panel for troubleshooting

**Key Functions:**
- `connectWebSocket()`: Establishes connection to WebSocket Proxy
- `toggleRecording()`: Toggles recording state (start/stop)
- `startRecording()`: Captures microphone audio and streams to API
- `stopRecording()`: Stops recording and commits audio buffer
- `handleRealtimeMessage()`: Processes responses from OpenAI
- `queueAudioChunk()`: Queues audio chunks for sequential playback
- `processAudioQueue()`: Plays audio chunks one at a time
- `playAudioChunk()`: Decodes and plays individual TTS audio chunks

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

## Environment Variables

```bash
OPENAI_API_KEY=your_openai_api_key  # Required for Realtime API
```

**WebSocket Proxy:**
Browsers don't support custom headers in WebSocket connections, so a FastAPI-based WebSocket proxy (`src/voice_screening_ui/proxy.py`) handles authentication:
- Proxy runs on port 8000 (configurable)
- Accepts WebSocket connections from browser
- Adds `Authorization` header and forwards to OpenAI Realtime API
- Bidirectional message forwarding
- Health check endpoint at `/health`

**Security:**
- API key stored in environment variables (not exposed to browser)
- Proxy handles all authentication server-side
- Use Streamlit secrets for API key management in production

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
3. Enter candidate email (optional for MVP)
4. Click "Start Interview"
5. Browser requests microphone permission
6. WebSocket connects to proxy (which connects to OpenAI Realtime API)
7. Agent greets candidate
8. User clicks mic button to start recording
9. User speaks, audio streams to OpenAI
10. Transcript appears in real-time
11. Agent responds with audio (played sequentially)
12. User clicks mic button again to stop and send
13. User clicks "End Interview"
14. Click "Analyze Interview" to get results
15. Optionally save results to database

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
├── app.py                    # Main Streamlit UI
├── proxy.py                  # WebSocket proxy for OpenAI authentication
├── analysis.py               # Simple analysis function
├── components/
│   ├── voice_interface.html  # HTML/JS for WebSocket and audio
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

**Known Limitations:**
- Uses deprecated `ScriptProcessor` API (should migrate to `AudioWorklet`)
- No authentication/authorization for UI access
- Simple error handling
- Limited session management
- Audio resampling may introduce slight latency (I'm new to this shit anyway)

## Future Enhancements

- Migrate from `ScriptProcessor` to `AudioWorklet` API
- Add authentication/authorization for UI access
- Add session persistence
- Improve error handling and reconnection logic
- Add recording playback
- Add interview question templates
- Optimize audio resampling performance
- Add audio level visualization
- Integrate with supervisor agent (if needed)
