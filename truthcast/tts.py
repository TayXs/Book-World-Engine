"""Turning the digest into something you can listen to.

The default provider is the browser: the web player speaks the script with the
device's own voice, which needs no key, no network round-trip and no audio
file on disk. Set TRUTHCAST_TTS_PROVIDER to elevenlabs or openai for a real
voice and a downloadable MP3.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import httpx

from .config import Settings, get_settings


class TTSError(RuntimeError):
    """Speech synthesis failed or is not configured."""


class BrowserVoice:
    """A no-op provider - the client speaks the text itself."""

    name = "browser"
    produces_file = False

    async def synthesize(self, text: str, target: Path) -> Path | None:
        return None


class ElevenLabsVoice:
    name = "elevenlabs"
    produces_file = True
    DEFAULT_VOICE = "21m00Tcm4TlvDq8ikWAM"

    async def synthesize(self, text: str, target: Path) -> Path:
        key = os.environ.get("ELEVENLABS_API_KEY")
        if not key:
            raise TTSError("ELEVENLABS_API_KEY is not set.")
        voice = os.environ.get("ELEVENLABS_VOICE_ID") or self.DEFAULT_VOICE
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice}",
                headers={"xi-api-key": key, "accept": "audio/mpeg"},
                json={
                    "text": text,
                    "model_id": "eleven_turbo_v2_5",
                    "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
                },
            )
        _raise_for_status(response, "ElevenLabs")
        target.write_bytes(response.content)
        return target


class OpenAIVoice:
    name = "openai"
    produces_file = True
    DEFAULT_VOICE = "alloy"

    async def synthesize(self, text: str, target: Path) -> Path:
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise TTSError("OPENAI_API_KEY is not set.")
        voice = os.environ.get("OPENAI_TTS_VOICE") or self.DEFAULT_VOICE
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/audio/speech",
                headers={"Authorization": f"Bearer {key}"},
                json={"model": "gpt-4o-mini-tts", "voice": voice, "input": text},
            )
        _raise_for_status(response, "OpenAI")
        target.write_bytes(response.content)
        return target


PROVIDERS = {
    BrowserVoice.name: BrowserVoice,
    ElevenLabsVoice.name: ElevenLabsVoice,
    OpenAIVoice.name: OpenAIVoice,
}


def get_provider(name: str | None = None, settings: Settings | None = None):
    settings = settings or get_settings()
    chosen = (name or settings.tts_provider or "browser").lower()
    provider = PROVIDERS.get(chosen)
    if provider is None:
        raise TTSError(
            f"Unknown TTS provider '{chosen}'. Choose one of: {', '.join(PROVIDERS)}."
        )
    return provider()


async def speak_text(
    text: str, settings: Settings | None = None, provider: str | None = None
) -> Path | None:
    """Render the script to an MP3, or None when the browser will speak it."""
    settings = settings or get_settings()
    settings.ensure_dirs()
    voice = get_provider(provider, settings)
    if not getattr(voice, "produces_file", False):
        return None

    digest = hashlib.sha256(f"{voice.name}:{text}".encode()).hexdigest()[:16]
    target = settings.audio_dir / f"{digest}.mp3"
    if target.exists() and target.stat().st_size > 0:
        return target  # same script, same voice - already rendered
    return await voice.synthesize(text, target)


def _raise_for_status(response: httpx.Response, label: str) -> None:
    if response.status_code >= 400:
        detail = response.text[:300]
        raise TTSError(f"{label} text-to-speech failed ({response.status_code}): {detail}")
