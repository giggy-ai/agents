"""Generate one WAV through the proposed native Giggy TTS plugin."""

from __future__ import annotations

import argparse
import asyncio
import wave
from pathlib import Path

import aiohttp

from livekit.plugins import giggy


async def generate(output: Path, *, allow_billable: bool = False) -> None:
    """Write one speech response; require explicit paid-request opt-in first.

    Args:
        output: WAV path to create.
        allow_billable: Authorize one intended provider synthesis request.
    """
    if not allow_billable:
        raise RuntimeError("Pass --allow-billable only after authorizing one synthesis request.")
    async with aiohttp.ClientSession() as session:
        provider = giggy.TTS(http_session=session)
        try:
            with wave.open(str(output), "wb") as wav:
                wav.setnchannels(provider.num_channels)
                wav.setsampwidth(2)
                wav.setframerate(provider.sample_rate)
                async with provider.synthesize("Hello from Giggy and LiveKit.") as stream:
                    async for event in stream:
                        wav.writeframesraw(bytes(event.frame.data))
        finally:
            await provider.aclose()


def main() -> None:
    """Parse the explicit billable opt-in and output path."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-billable", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("speech.wav"))
    args = parser.parse_args()
    asyncio.run(generate(args.output, allow_billable=args.allow_billable))


if __name__ == "__main__":
    main()
