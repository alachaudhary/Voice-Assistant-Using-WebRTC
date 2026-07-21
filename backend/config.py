from dotenv import load_dotenv
import os

load_dotenv()

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_BASE = os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "gpt-4o-mini")
OPENROUTER_SYSTEM_PROMPT = os.getenv(
    "OPENROUTER_SYSTEM_PROMPT",
    "You are a helpful assistant for live voice conversations. Respond succinctly and help the user based on the transcript provided.",
)

SOUNDDEVICE_DEVICE = os.getenv("SOUNDDEVICE_DEVICE")

ELEVEN_LABS_API_KEY = os.getenv("ELEVEN_LABS_API_KEY")
ELEVEN_LABS_VOICE_ID = os.getenv("ELEVEN_LABS_VOICE_ID")  
ELEVEN_LABS_API_BASE = os.getenv("ELEVEN_LABS_API_BASE")
ELEVENLABS_OUTPUT_FORMAT = "pcm_24000"