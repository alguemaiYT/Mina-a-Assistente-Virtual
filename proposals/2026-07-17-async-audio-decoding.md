# Async Audio Decoding

## Summary

Offload synchronous `miniaudio.decode` operations in `src/utils/tts_client.py` to `asyncio.to_thread` to prevent blocking the async event loop.

## Problem

The method `TTSClient.play` in `src/utils/tts_client.py` calls `miniaudio.decode(audio_bytes, output_format=miniaudio.SampleFormat.SIGNED16)`. `miniaudio.decode` is a synchronous, CPU-bound operation. When called directly within the `async` method `play`, it blocks the asyncio event loop for the duration of the decoding process. This can cause stuttering or lagging in the user interface or delay the processing of other asynchronous tasks, such as wake word detection or streaming STT responses.

## Evidence

In `src/utils/tts_client.py` around line 249:
```python
    async def play(self, audio_bytes: bytes, on_start: Optional[Callable] = None) -> None:
        """Play MP3 bytes through the persistent output device (0ms latency, no cutoff)."""
        if not _HAS_MINIAUDIO or not audio_bytes:
            return
        async with self._audio_lock:
            try:
                decoded = miniaudio.decode(audio_bytes, output_format=miniaudio.SampleFormat.SIGNED16)
```
The call to `miniaudio.decode` is synchronous and blocks the thread running the event loop.

## Proposed Solution

Wrap the call to `miniaudio.decode` in `asyncio.to_thread` so that it runs in a background thread, preventing it from blocking the main event loop.

Change this:
```python
decoded = miniaudio.decode(audio_bytes, output_format=miniaudio.SampleFormat.SIGNED16)
```
To this:
```python
decoded = await asyncio.to_thread(miniaudio.decode, audio_bytes, output_format=miniaudio.SampleFormat.SIGNED16)
```

## Benefits

- Prevents blocking the asyncio event loop.
- Improves application responsiveness and reduces potential lag in UI or background tasks.
- Adheres to best practices for handling CPU-bound tasks in async applications.

## Trade-offs

- Slight overhead of spinning up or communicating with a worker thread.

## Risks

- Low risk, assuming `miniaudio.decode` does not have any thread-safety issues when called concurrently from different threads (which is highly unlikely, as it's a stateless CPU-bound function).

## Estimated Complexity

- Low

## Priority

- Medium

## Success Criteria

- The application's asyncio event loop remains responsive during audio playback.
- There are no regressions in audio quality or playback functionality.

## Open Questions

- Are there any other synchronous operations in the TTS client that should be offloaded?
