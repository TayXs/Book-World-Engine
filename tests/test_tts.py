import pytest

from truthcast.tts import BrowserVoice, ElevenLabsVoice, TTSError, get_provider, speak_text


def test_the_default_provider_speaks_in_the_browser(settings):
    assert isinstance(get_provider(None, settings), BrowserVoice)


def test_providers_can_be_chosen_by_name(settings):
    assert isinstance(get_provider("elevenlabs", settings), ElevenLabsVoice)


def test_an_unknown_provider_says_what_is_available(settings):
    with pytest.raises(TTSError, match="browser"):
        get_provider("robot-voice-9000", settings)


@pytest.mark.asyncio
async def test_browser_provider_writes_no_file(settings):
    assert await speak_text("Hello there.", settings=settings) is None


@pytest.mark.asyncio
async def test_a_missing_api_key_is_reported_clearly(settings, monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    settings.tts_provider = "elevenlabs"
    with pytest.raises(TTSError, match="ELEVENLABS_API_KEY"):
        await speak_text("Hello there.", settings=settings)


@pytest.mark.asyncio
async def test_the_same_script_is_not_re_rendered(settings, monkeypatch):
    settings.tts_provider = "elevenlabs"
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key")
    calls = []

    async def fake_synthesize(self, text, target):
        calls.append(text)
        target.write_bytes(b"audio")
        return target

    monkeypatch.setattr(ElevenLabsVoice, "synthesize", fake_synthesize)

    first = await speak_text("Hello there.", settings=settings)
    second = await speak_text("Hello there.", settings=settings)
    assert first == second and len(calls) == 1
