import importlib.util
import wave
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

pytestmark = pytest.mark.unit

spec = importlib.util.spec_from_file_location(
    "giggy_first_speech",
    Path(__file__).resolve().parents[3] / "examples/voice_agents/giggy_speech.py",
)
assert spec and spec.loader
example = importlib.util.module_from_spec(spec)
spec.loader.exec_module(example)


@pytest.mark.asyncio
async def test_first_speech_requires_opt_in_before_provider_creation(monkeypatch, tmp_path):
    factory = Mock()
    monkeypatch.setattr(example.giggy, "TTS", factory)
    with pytest.raises(RuntimeError, match="authorizing"):
        await example.generate(tmp_path / "speech.wav")
    factory.assert_not_called()
    assert not (tmp_path / "speech.wav").exists()


@pytest.mark.asyncio
async def test_first_speech_wav_and_cleanup(monkeypatch, tmp_path):
    class Stream:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        def __aiter__(self):
            return self.frames()

        async def frames(self):
            yield SimpleNamespace(frame=SimpleNamespace(data=b"\x01\x02" * 2400))

    provider = SimpleNamespace(
        sample_rate=24000,
        num_channels=1,
        synthesize=Mock(return_value=Stream()),
        aclose=AsyncMock(),
    )
    monkeypatch.setattr(example.giggy, "TTS", Mock(return_value=provider))
    output = tmp_path / "speech.wav"
    await example.generate(output, allow_billable=True)
    with wave.open(str(output), "rb") as wav:
        assert wav.getframerate() == 24000
        assert wav.getnchannels() == 1
        assert wav.getnframes() == 2400
    provider.synthesize.assert_called_once()
    provider.aclose.assert_awaited_once()
