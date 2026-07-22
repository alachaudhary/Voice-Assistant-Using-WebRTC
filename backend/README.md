# 🎙️ AI Voice Assistant (Browser ↔ WebRTC ↔ Python)

A real-time AI Voice Assistant built from scratch using **WebRTC**, **FastAPI**, **Deepgram Speech-to-Text**, **LLM**, and **ElevenLabs Text-to-Speech**.

Unlike many projects that rely on third-party platforms such as LiveKit, this project implements the WebRTC signaling and media pipeline manually to better understand how browser-based voice assistants work internally.

---

## Features

- 🎤 Browser microphone access
- 🌐 WebRTC audio streaming
- 🔄 Manual WebRTC signaling using WebSockets
- 🗣️ Real-time Speech-to-Text with Deepgram
- 🤖 LLM conversation engine
- 🔊 Text-to-Speech using ElevenLabs
- 💬 Live chat interface
- 📱 Responsive frontend
- ⚡ Low-latency streaming

---

## Project Structure

```text
voice-agent/
│
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
│
├── backend/
│   ├── main.py
│   ├── deepgram_stt.py
│   ├── llm.py
│   ├── eleven_labs_tts.py
│   ├── config.py
│   └── requirements.txt
│
├── .env
└── README.md
```

---

## Architecture

```text
                 Browser
                    │
            Microphone Access
                    │
                WebRTC Audio
                    │
                    ▼
          FastAPI + aiortc Server
                    │
                    ▼
         Deepgram Streaming API
                    │
              Live Transcript
                    │
                    ▼
                  LLM
                    │
              AI Response
                    │
                    ▼
           ElevenLabs TTS
                    │
            WebRTC Audio Track
                    │
                    ▼
                 Browser
```

---

## Tech Stack

### Frontend

- HTML5
- CSS3
- JavaScript
- WebRTC API

### Backend

- Python
- FastAPI
- aiortc
- WebSockets

### AI Services

- Deepgram STT
- LLM (OpenRouter/OpenAI/Groq compatible)
- ElevenLabs TTS

---

## Workflow

1. User grants microphone permission.
2. Browser captures microphone audio.
3. Audio is streamed to the backend using WebRTC.
4. Backend forwards PCM audio to Deepgram.
5. Deepgram returns live transcripts.
6. Transcript is sent to the LLM.
7. LLM generates a response.
8. ElevenLabs synthesizes speech.
9. Audio is streamed back to the browser.

---

## Installation

### Clone Repository

```bash
git clone https://github.com/yourusername/voice-agent.git
cd voice-agent
```

### Create Virtual Environment

```bash
python -m venv .venv
```

### Activate

Windows

```bash
.venv\Scripts\activate
```

Linux / macOS

```bash
source .venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file.

```env
DEEPGRAM_API_KEY=YOUR_API_KEY

ELEVEN_LABS_API_KEY=YOUR_API_KEY
ELEVEN_LABS_VOICE_ID=YOUR_VOICE_ID

OPENROUTER_API_KEY=YOUR_API_KEY
OPENROUTER_MODEL=YOUR_MODEL
```

---

## Run Backend

```bash
python main.py
```

Backend runs on

```
http://localhost:8000
```

---

## Open Frontend

Open

```
frontend/index.html
```

or serve it with a local web server.

---

## Current Status

### Completed

- Browser UI
- WebRTC signaling
- FastAPI backend
- Browser microphone capture
- Deepgram integration
- LLM integration
- ElevenLabs integration

### In Progress

- Browser audio playback via WebRTC
- Echo cancellation improvements
- Conversation state management
- Production deployment

---

## Learning Goals

This project focuses on understanding how real-time voice assistants work under the hood by implementing:

- WebRTC
- SDP Offer/Answer
- ICE Candidates
- Audio streaming
- Speech recognition
- LLM orchestration
- Audio synthesis
- Real-time communication

without relying on higher-level orchestration frameworks.

---

## Future Improvements

- Voice Activity Detection (VAD)
- Function Calling
- Tool Use
- Memory
- Interruptions (Bararge-In)
- Multi-user support
- Authentication
- Noise suppression
- Docker deployment
- HTTPS deployment
- TURN server support

---

## License

MIT License

---

## Author

**Abd Ul Ala Taha**

Machine Learning Engineer

GitHub: https://github.com/yourusername