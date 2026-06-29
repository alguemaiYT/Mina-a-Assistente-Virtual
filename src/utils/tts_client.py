"""
TTS Client — Direct local edge-tts integration inside the application.

Synthesises audio in the background directly inside the python client, using edge-tts.
Eliminates the FastAPI HTTP server daemon and reduces latency.
"""

import asyncio
import io
import time
import hashlib
from typing import Optional

from src.utils.logging_config import get_logger

logger = get_logger(__name__)

try:
    import miniaudio
    _HAS_MINIAUDIO = True
except ImportError:
    _HAS_MINIAUDIO = False
    logger.warning("miniaudio not installed — TTS playback disabled")

try:
    import edge_tts
    _HAS_EDGE_TTS = True
except ImportError:
    _HAS_EDGE_TTS = False
    logger.warning("edge-tts not installed — TTS synthesis disabled")


class TTSClient:
    """Direct, embedded wrapper around the local edge-tts engine."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",  # Kept for compatibility with views
        enabled: bool = True,
        voice: str = "pt-BR-FranciscaNeural",
        rate: str = "+15%",
        pitch: str = "+3Hz",
        volume: str = "+0%",
    ):
        self._enabled = enabled and _HAS_MINIAUDIO and _HAS_EDGE_TTS
        self._voice = voice
        self._rate = rate
        self._pitch = pitch
        self._volume = volume
        self._audio_lock = asyncio.Lock()
        self._cache: dict[str, bytes] = {}
        self._cache_max = 128

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def enabled(self) -> bool:
        return self._enabled

    # ------------------------------------------------------------------
    # Embedding Management
    # ------------------------------------------------------------------

    async def close(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    async def health_check(self) -> bool:
        """Verify the edge-tts local module functions properly."""
        if not self._enabled:
            return False
        try:
            # Test if edge_tts can query voices (requires internet access)
            await edge_tts.list_voices()
            logger.info("Local embedded TTS engine initialized (voice=%s)", self._voice)
            return True
        except Exception as exc:
            logger.warning("Embedded TTS engine check failed (no internet?): %s", exc)
        self._enabled = False
        return False

    # ------------------------------------------------------------------
    # Synthesis
    # ------------------------------------------------------------------

    def pre_synthesize(self, text: str) -> Optional[asyncio.Task]:
        """Fire-and-forget synthesis — returns a Task that resolves to bytes."""
        if not self._enabled or not text.strip():
            return None
        return asyncio.create_task(self._fetch_audio(text))

    def _cache_key(self, text: str) -> str:
        raw = f"{text}|{self._voice}|{self._rate}|{self._pitch}|{self._volume}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    async def _fetch_audio(self, text: str) -> Optional[bytes]:
        """Synthesize MP3 bytes directly using edge_tts (non-blocking)."""
        key = self._cache_key(text)
        if key in self._cache:
            logger.debug("TTS cache hit for: '%s'", text[:30])
            return self._cache[key]

        try:
            t0 = time.perf_counter()
            communicate = edge_tts.Communicate(
                text,
                self._voice,
                rate=self._rate,
                pitch=self._pitch,
                volume=self._volume
            )
            buf = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    buf.write(chunk["data"])
            audio = buf.getvalue()

            elapsed = time.perf_counter() - t0
            logger.info("TTS local synthesis OK | chars=%d | latency=%.3fs | cache=%d", len(text), elapsed, len(self._cache))

            if len(self._cache) >= self._cache_max:
                oldest = next(iter(self._cache))
                del self._cache[oldest]
            self._cache[key] = audio
            return audio
        except Exception as exc:
            logger.warning("Local TTS synthesis error: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Playback
    # ------------------------------------------------------------------

    async def play(self, audio_bytes: bytes) -> None:
        """Play MP3 bytes through the default output device (no overlap)."""
        if not _HAS_MINIAUDIO or not audio_bytes:
            return
        async with self._audio_lock:
            try:
                await asyncio.to_thread(self._play_sync, audio_bytes)
            except Exception as exc:
                logger.warning("TTS playback error: %s", exc)

    @staticmethod
    def _play_sync(audio_bytes: bytes) -> None:
        """Decode MP3 and play synchronously (runs in a worker thread)."""
        decoded = miniaudio.decode(audio_bytes, output_format=miniaudio.SampleFormat.SIGNED16)
        if not decoded.samples or decoded.num_frames == 0:
            return

        duration_s = decoded.num_frames / decoded.sample_rate
        nch = decoded.nchannels
        samples = decoded.samples
        total = len(samples)
        pos = [0]

        def _generator():
            required = yield b""
            while pos[0] < total:
                n = required * nch
                chunk = samples[pos[0] : pos[0] + n]
                pos[0] += n
                if not chunk:
                    break
                required = yield chunk

        gen = _generator()
        next(gen)

        device = miniaudio.PlaybackDevice(
            output_format=miniaudio.SampleFormat.SIGNED16,
            nchannels=nch,
            sample_rate=decoded.sample_rate,
        )
        try:
            device.start(gen)
            time.sleep(duration_s + 0.08)
        finally:
            device.close()
