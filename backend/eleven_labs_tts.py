import json
import sys
import urllib.error
import urllib.request
from typing import Optional

import numpy as np



from config import (
    ELEVEN_LABS_API_KEY,
    ELEVEN_LABS_VOICE_ID,
    ELEVEN_LABS_API_BASE,
)


class ElevenLabsTTS:
    """Text-to-Speech synthesis using ElevenLabs API with audio playback."""

    def __init__(
        self,
        api_key: str = ELEVEN_LABS_API_KEY,
        voice_id: str = ELEVEN_LABS_VOICE_ID,
        api_base: str = ELEVEN_LABS_API_BASE,
        model: str = "eleven_v3",
        sample_rate: int = 24000,
    ):
        if not api_key:
            raise ValueError(
                "Missing ElevenLabs API key. Set ELEVEN_LABS_API_KEY in .env or the environment."
            )

        self.api_key = api_key
        self.voice_id = voice_id
        self.api_base = api_base.rstrip("/")
        self.model = model
        self.sample_rate = sample_rate

   
    def _build_url(self) -> str:
        """Build the text-to-speech API endpoint URL."""
        return (
          f"{self.api_base}/v1/text-to-speech/"
          f"{self.voice_id}?output_format=pcm_24000"
       )
    def _build_payload(
        self,
        text: str,
        stability: float = 0.5,
        similarity_boost: float = 0.75,
    ) -> dict:
        """Build the request payload for ElevenLabs API."""
        return {
            "text": text,
            "model_id": self.model,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
            },
        }

    def synthesize(
        self,
        text: str,
        stability: float = 0.5,
        similarity_boost: float = 0.75,
    ) -> Optional[bytes]:
        """
        Synthesize text to speech and return audio bytes.

        Args:
            text: The text to synthesize
            stability: Voice stability parameter (0.0 to 1.0)
            similarity_boost: Similarity boost parameter (0.0 to 1.0)

        Returns:
            Audio bytes in MP3 format, or None if synthesis failed
        """
        if not text or not text.strip():
            print("Warning: Empty text provided to TTS", file=sys.stderr)
            return None

        url = self._build_url()
        payload = self._build_payload(text, stability, similarity_boost)

        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "xi-api-key": self.api_key,
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                
                print("Status:", response.status)
                print("Content-Type:", response.headers.get("Content-Type"))
                print("Content-Length:", response.headers.get("Content-Length"))

                audio_bytes = response.read()

                print("First 16 bytes:", audio_bytes[:16])

                return audio_bytes
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8")
            print(
                f"ElevenLabs TTS request failed: {exc.code} {exc.reason} - {error_body}",
                file=sys.stderr,
            )
            return None
        except urllib.error.URLError as exc:
            print(
                f"ElevenLabs TTS request failed: {exc}. Verify network/DNS and ELEVEN_LABS_API_BASE.",
                file=sys.stderr,
            )
            return None
        except Exception as exc:
            print(f"Unexpected error during TTS synthesis: {exc}", file=sys.stderr)
            return None

    def speak(
    self,
    text: str,
    stability: float = 0.5,
    similarity_boost: float = 0.75,
    ) -> bool:

        audio_bytes = self.synthesize(text, stability, similarity_boost)

        if not audio_bytes:
            return False

        print(f"TTS generated {len(audio_bytes)} bytes")

        # TODO: Send these bytes over WebRTC
        return True
    def save_audio(self, text: str, output_path: str, stability: float = 0.5, similarity_boost: float = 0.75) -> bool:
        """
        Synthesize text and save to an MP3 file.

        Args:
            text: The text to synthesize
            output_path: Path where to save the MP3 file
            stability: Voice stability parameter (0.0 to 1.0)
            similarity_boost: Similarity boost parameter (0.0 to 1.0)

        Returns:
            True if successful, False otherwise
        """
        audio_bytes = self.synthesize(text, stability, similarity_boost)
        if not audio_bytes:
            return False

        try:
            with open(output_path, "wb") as f:
                f.write(audio_bytes)
            print(f"Audio saved to {output_path}")
            return True
        except Exception as exc:
            print(f"Error saving audio to {output_path}: {exc}", file=sys.stderr)
            return False


if __name__ == "__main__":
    tts = ElevenLabsTTS()
    text = "Hello! This is a test of the ElevenLabs text to speech API."
    print(f"Synthesizing: {text}")

    if tts.speak(text):
        print("Audio played successfully!")
    else:
        print("Failed to play audio. Attempting to save to file instead...")
        if tts.save_audio(text, "output.mp3"):
            print("Audio saved to output.mp3")
