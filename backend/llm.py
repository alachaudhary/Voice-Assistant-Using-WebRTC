import json
import urllib.error
import urllib.request
from typing import Dict, List, Optional

from config import (
    OPENROUTER_API_BASE,
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
    OPENROUTER_SYSTEM_PROMPT,
)


class ChatClient:
    def __init__(
        self,
        api_key: str = OPENROUTER_API_KEY,
        api_base: str = OPENROUTER_API_BASE,
        model: str = OPENROUTER_MODEL,
        system_prompt: str = OPENROUTER_SYSTEM_PROMPT,
    ):
        self.provider = "openrouter"
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.model = model
        self.system_prompt = system_prompt
        self.tts_client = None

        if not self.api_key:
            raise ValueError(
                "Missing OpenRouter API key. Set OPENROUTER_API_KEY in .env or the environment."
            )

    def set_tts_client(self, tts_client) -> None:
        """Set the TTS client to automatically speak responses."""
        self.tts_client = tts_client

    def build_messages(self, history: List[Dict[str, str]], user_message: str) -> List[Dict[str, str]]:
        messages = [
            {"role": "system", "content": self.system_prompt},
        ]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        return messages

    def _build_payload(
        self,
        history: List[Dict[str, str]],
        user_message: str,
        temperature: float,
        max_tokens: int,
    ) -> Dict[str, object]:
        return {
            "model": self.model,
            "messages": self.build_messages(history, user_message),
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

    def _parse_response(self, result: Dict[str, object]) -> str:
        if not isinstance(result, dict):
            raise RuntimeError("Invalid OpenRouter response format")

        choices = result.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("OpenRouter response contained no choices")

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise RuntimeError("OpenRouter response choice format invalid")

        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise RuntimeError("OpenRouter response message format invalid")

        content = message.get("content")
        if not isinstance(content, str):
            raise RuntimeError("OpenRouter response content missing")

        return content.strip()

    def _build_chat_url(self) -> str:
        base = self.api_base.rstrip("/")
        if base.endswith("/chat/completions"):
            return base
        if base.endswith("/v1"):
            return f"{base}/chat/completions"
        return f"{base}/chat/completions"

    def create_chat_completion(
        self,
        history: List[Dict[str, str]],
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 800,
    ) -> str:
        url = self._build_chat_url()
        payload = self._build_payload(history, user_message, temperature, max_tokens)

        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + self.api_key,
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = response.read().decode("utf-8")
                result = json.loads(body)
                assistant_text = self._parse_response(result)
                return assistant_text.strip()
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8")
            raise RuntimeError(
                f"LLM request to {url} failed: {exc.code} {exc.reason} - {error_body}"
            )
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"LLM request to {url} failed: {exc}. Verify network/DNS and OPENROUTER_API_BASE."
            )


class ConversationHistory:
    def __init__(self, max_messages: int = 20):
        self._messages: List[Dict[str, str]] = []
        self.max_messages = max_messages

    @property
    def messages(self) -> List[Dict[str, str]]:
        return list(self._messages)

    def add_user_message(self, text: str) -> None:
        self._messages.append({"role": "user", "content": text})
        self._truncate_history()

    def add_assistant_message(self, text: str) -> None:
        self._messages.append({"role": "assistant", "content": text})
        self._truncate_history()

    def _truncate_history(self) -> None:
        if len(self._messages) <= self.max_messages:
            return
        self._messages = self._messages[-self.max_messages:]


def create_default_conversation_history(max_messages: int = 20) -> ConversationHistory:
    return ConversationHistory(max_messages=max_messages)
