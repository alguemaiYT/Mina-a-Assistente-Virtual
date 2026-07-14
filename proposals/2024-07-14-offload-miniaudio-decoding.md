# Offload miniaudio.decode to Background Thread

## Summary

This proposal suggests offloading the synchronous, CPU-bound `miniaudio.decode` operation in `src/utils/tts_client.py` to a background worker thread using `asyncio.to_thread`.

## Problem

Currently, the `TTSClient.play` method in `src/utils/tts_client.py` performs audio decoding synchronously on the main asyncio event loop using `miniaudio.decode`. Audio decoding is a CPU-bound operation. Executing it directly within an `async` function blocks the event loop, delaying the execution of other concurrent tasks, such as UI updates, network requests, and wake word detection.

## Evidence

In `src/utils/tts_client.py`, the `play` method contains the following synchronous call:

```python
decoded = miniaudio.decode(audio_bytes, output_format=miniaudio.SampleFormat.SIGNED16)
```

This code is inside the `async def play(...)` method and is executed directly on the main event loop, potentially causing latency spikes during TTS playback.

## Proposed Solution

Modify the `play` method in `src/utils/tts_client.py` to offload the decoding step to a background thread. This can be achieved natively in modern Python using `asyncio.to_thread()`.

```python
# Instead of:
# decoded = miniaudio.decode(audio_bytes, output_format=miniaudio.SampleFormat.SIGNED16)

# Use:
# decoded = await asyncio.to_thread(
#     miniaudio.decode, audio_bytes, output_format=miniaudio.SampleFormat.SIGNED16
# )
```

## Benefits

- **Performance:** Prevents the main asyncio event loop from stalling during audio decoding.
- **Responsiveness:** Improves UI responsiveness and background task reliability (e.g., wake word monitoring, incoming network requests) during TTS playback.

## Trade-offs

- **Slight Overhead:** Thread creation and context switching introduce a negligible overhead compared to the cost of blocking the event loop.

## Risks

- **Low:** `miniaudio.decode` does not mutate shared global state and relies purely on the input bytes, making it highly safe to execute concurrently in a thread.

## Estimated Complexity

- Low

## Priority

- High

## Success Criteria

- The application can decode large audio payloads without causing noticeable stalls in the GUI or other asynchronous components.
- No exceptions are thrown during decoding in the background thread.

## Open Questions

- Should we apply this pattern to other CPU-bound operations in the project to further improve event loop hygiene?
