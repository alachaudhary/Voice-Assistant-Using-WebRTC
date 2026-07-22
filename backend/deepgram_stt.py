import sys
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from deepgram import DeepgramClient
from deepgram.core.events import EventType

from config import DEEPGRAM_API_KEY
from llm import ChatClient, ConversationHistory


class DeepgramLiveTranscriber:
    """Live microphone transcription using Deepgram's streaming WebSocket API."""

    def __init__(
        self,
        api_key: str = DEEPGRAM_API_KEY,
        sample_rate: int = 16000,
        channels: int = 1,
        model: str = "flux-general-en",
        language: str = "en",
        encoding: str = "linear16",
        device: Optional[Any] = None,
        utterance_end_ms: int = 500,
        llm_history_size: int = 20,
        
    ):
        if not api_key:
            raise ValueError(
                "Missing Deepgram API key. Set DEEPGRAM_API_KEY in .env or the environment."
            )

        self.sample_rate = sample_rate
        self.channels = channels
        self.model = model
        self.language = language
        self.encoding = encoding
        self.device = device
        self.utterance_end_ms = utterance_end_ms
        self.current_transcript = ""
        self.last_sent_transcript = ""
        if self.utterance_end_ms < 500:
            print(
                "Warning: Deepgram v2 eot_timeout_ms must be between 500 and 60000 ms. Using 500 ms.",
                file=sys.stderr,
            )
            self.utterance_end_ms = 500
        self.client = DeepgramClient(api_key=api_key)
        self.socket = None
        self.llm = ChatClient()
        self.conversation_history = ConversationHistory(max_messages=llm_history_size)
        self.tts = None
        self.tts_track = None
        self.is_tts_playing = False
        self._pending_final_transcript: Optional[str] = None

    def set_tts_client(self, tts_client) -> None:
        """Set the TTS client to automatically speak responses."""
        self.tts = tts_client

    def set_tts_track(self, tts_track) -> None:
        """Set the WebRTC TTS track."""
        self.tts_track = tts_track

    

    def _extract_transcript(self, response):
        """Extract transcript text from Deepgram listen response objects."""
        if response is None:
            return None

        # Handle Deepgram v1 socket response objects and raw dictionaries.
        if isinstance(response, dict):
            data = response
        else:
            data = {}
            if hasattr(response, "type"):
                data["type"] = getattr(response, "type")
            if hasattr(response, "channel"):
                data["channel"] = getattr(response, "channel")
            if hasattr(response, "results"):
                data["results"] = getattr(response, "results")

        transcript = None

        if data.get("type") == "Results":
            channel = data.get("channel")
            if channel is None and isinstance(response, dict):
                channel = response.get("channel")

            if channel is not None:
                alternatives = None
                if isinstance(channel, dict):
                    alternatives = channel.get("alternatives")
                elif hasattr(channel, "alternatives"):
                    alternatives = getattr(channel, "alternatives")

                if alternatives:
                    first_alt = alternatives[0]
                    if isinstance(first_alt, dict):
                        transcript = first_alt.get("transcript")
                    elif hasattr(first_alt, "transcript"):
                        transcript = getattr(first_alt, "transcript")
                    return transcript.strip() if transcript else None

        results = data.get("results")
        if results is None and isinstance(response, dict):
            results = response.get("results")

        if results is not None:
            channels = None
            if isinstance(results, dict):
                channels = results.get("channels")
            elif hasattr(results, "channels"):
                channels = getattr(results, "channels")

            if channels:
                first_channel = channels[0]
                alternatives = None
                if isinstance(first_channel, dict):
                    alternatives = first_channel.get("alternatives")
                elif hasattr(first_channel, "alternatives"):
                    alternatives = getattr(first_channel, "alternatives")

                if alternatives:
                    first_alt = alternatives[0]
                    if isinstance(first_alt, dict):
                        transcript = first_alt.get("transcript")
                    elif hasattr(first_alt, "transcript"):
                        transcript = getattr(first_alt, "transcript")
                    return transcript.strip() if transcript else None

        # Handle Deepgram v2 TurnInfo responses.
        if data.get("type") == "TurnInfo":
            transcript = None
            if isinstance(response, dict):
                transcript = response.get("transcript")
            elif hasattr(response, "transcript"):
                transcript = getattr(response, "transcript")
            return transcript.strip() if transcript else None

        return None

    def _get_message_type_and_event(self, response) -> Tuple[Optional[str], Optional[str]]:
        message_type = None
        event = None

        if isinstance(response, dict):
            message_type = response.get("type")
            event = response.get("event")
        else:
            if hasattr(response, "type"):
                message_type = getattr(response, "type")
            if hasattr(response, "event"):
                event = getattr(response, "event")

        return message_type, event

    def _is_final_message(self, response) -> bool:
        if response is None:
            return False

        if hasattr(response, "speech_final"):
            return bool(getattr(response, "speech_final"))
        if hasattr(response, "is_final"):
            return bool(getattr(response, "is_final"))

        message_type, event = self._get_message_type_and_event(response)
        if message_type == "UtteranceEnd":
            return True
        if message_type == "TurnInfo" and event == "EndOfTurn":
            return True

        if isinstance(response, dict):
            if response.get("speech_final") is True or response.get("is_final") is True:
                return True
            if response.get("type") == "UtteranceEnd":
                return True
            if response.get("type") == "TurnInfo" and response.get("event") == "EndOfTurn":
                return True

        return False

    def _send_pending_transcript_to_llm(self) -> None:
        transcript = self._pending_final_transcript

        if not transcript:
            return

        # Remember what was sent
        self.last_sent_transcript = transcript

        # Clear buffers so silence doesn't resend
        self.current_transcript = ""
        self._pending_final_transcript = None

        worker = threading.Thread(
            target=self._handle_final_user_transcript,
            args=(transcript,),
            daemon=True,
        )
        worker.start()

    def _handle_final_user_transcript(self, transcript: str) -> None:
        transcript = transcript.strip()
        if not transcript:
            return

        print("[LLM] sending final transcript to LLM:", transcript)
        self.conversation_history.add_user_message(transcript)
        try:
            assistant_text = self.llm.create_chat_completion(
                self.conversation_history.messages,
                transcript,
            )
        except Exception as exc:
            print("LLM request failed:", exc, file=sys.stderr)
            return

        self.conversation_history.add_assistant_message(assistant_text)
        print("[Assistant]", assistant_text)

        if self.tts:
            print("[TTS] synthesizing response...")

            self.is_tts_playing = True

            try:
                audio = self.tts.synthesize(assistant_text)
                print("Received", len(audio), "bytes")
                print("Seconds:", len(audio) / (24000 * 2))

                if audio and self.tts_track:
                    self.tts_track.enqueue(audio)
            finally:
                self.is_tts_playing = False

    def _on_open(self, _event):
        print("Connected to Deepgram live transcription.")
        print(f"Using LLM provider: {self.llm.provider}")
        try:
            print(f"LLM endpoint: {self.llm._build_chat_url()}")
        except Exception as exc:
            print(f"Unable to resolve LLM endpoint: {exc}", file=sys.stderr)

    def _on_message(self, message):
        print(message)
        # Ignore microphone input while TTS is speaking
        if self.is_tts_playing:
            return

        transcript = self._extract_transcript(message)
        is_final = self._is_final_message(message)
        message_type, event = self._get_message_type_and_event(message)

        # Save the latest transcript
        if transcript:
            transcript = transcript.strip()

            if transcript:
                self.current_transcript = transcript

        # Debug output
        if transcript:
            label = "Final" if is_final else "Interim"
            print(f"[Deepgram {label}] {transcript}")
        else:
            print(
                f"[Deepgram] message received type={message_type!r} event={event!r} with no transcript"
            )

        # Final transcript received
        if is_final:

            # Nothing to send
            if not self.current_transcript:
                return

            # Prevent duplicate sends
            if self.current_transcript == self.last_sent_transcript:
                print("[Deepgram] Duplicate transcript ignored.")
                return

            # Save the COMPLETE sentence
            self._pending_final_transcript = self.current_transcript

            # Flux v2 EndOfTurn
            if message_type == "TurnInfo" and event == "EndOfTurn":
                print("[Deepgram] End of turn received.")
                self._send_pending_transcript_to_llm()
                return

            # v1 UtteranceEnd
            if message_type == "UtteranceEnd":
                print("[Deepgram] Utterance end received.")
                self._send_pending_transcript_to_llm()
                return

            print("[Deepgram] Waiting for EndOfTurn...")
            return

        # Some Deepgram versions send EndOfTurn separately
        if (
            message_type == "TurnInfo"
            and event == "EndOfTurn"
            and self._pending_final_transcript
        ):
            print("[Deepgram] End of turn received.")
            self._send_pending_transcript_to_llm()
            return

        if (
            message_type == "UtteranceEnd"
            and self._pending_final_transcript
        ):
            print("[Deepgram] Utterance end received.")
            self._send_pending_transcript_to_llm()
            return
    def _on_error(self, error):
        print("Deepgram error:", error, file=sys.stderr)

    def _on_close(self, _event):
        print("Deepgram connection closed.")

   

    def _listen_socket(self):
        if self.socket is None:
            return
        self.socket.start_listening()
        
    def start(self):

        connect_kwargs = {
        "model": self.model,
        "encoding": self.encoding,
        "sample_rate": self.sample_rate,
        "eot_timeout_ms": self.utterance_end_ms,
    }

        if self.model == "flux-general-multi" and self.language:
            connect_kwargs["language_hint"] = self.language

        # Keep the context manager alive
        self.socket_context = self.client.listen.v2.connect(**connect_kwargs)

        # Enter the context manually
        self.socket = self.socket_context.__enter__()

        self.socket.on(EventType.OPEN, self._on_open)
        self.socket.on(EventType.MESSAGE, self._on_message)
        self.socket.on(EventType.ERROR, self._on_error)
        self.socket.on(EventType.CLOSE, self._on_close)

        listener = threading.Thread(
            target=self._listen_socket,
            daemon=True,
        )

        listener.start()

    def stop(self):

        if self.socket:
            try:
                self.socket.send_close_stream()
            except Exception:
                pass

        if hasattr(self, "socket_context"):
            self.socket_context.__exit__(None, None, None)
    def send_audio(self, audio_bytes: bytes):
        if self.is_tts_playing:
            return

        if not self.socket:
            return

        self.socket.send_media(audio_bytes)
        


