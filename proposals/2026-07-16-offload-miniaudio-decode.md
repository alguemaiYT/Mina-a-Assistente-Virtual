# Offload synchronous `miniaudio.decode` to background thread

## Summary

Move the synchronous execution of `miniaudio.decode` to a background worker thread using `asyncio.to_thread` to prevent blocking the asyncio event loop.

## Problem

The application performs audio decoding using `miniaudio.decode` synchronously within the asyncio event loop. Since audio decoding can be CPU-bound and time-consuming, this operation blocks the event loop, potentially causing UI freezes, missed events, and reduced responsiveness in asynchronous tasks.

## Evidence

In `src/utils/tts_client.py` at line 249, `miniaudio.decode` is called synchronously inside an `async def` method:
`decoded = miniaudio.decode(audio_bytes, output_format=miniaudio.SampleFormat.SIGNED16)`

## Proposed Solution

Wrap the `miniaudio.decode` call with `asyncio.to_thread` to execute it in a separate thread, offloading the CPU-intensive work from the main event loop.

## Benefits

- Prevents UI freezes and improves overall application responsiveness.
- Ensures smooth execution of other concurrent asynchronous tasks.
- Better adherence to asynchronous programming best practices.

## Trade-offs

- Slight overhead from creating and managing a background thread, though this is negligible compared to the benefits.

## Risks

- Thread-safety concerns if the audio data or shared state is modified concurrently, although `asyncio.to_thread` mitigates this for simple function calls without shared mutable state.

## Estimated Complexity

- Low

## Priority

- High

## Success Criteria

- The `miniaudio.decode` call is executed asynchronously using `asyncio.to_thread`.
- No noticeable UI freezes or event loop blocking occurs during audio decoding.

## Open Questions

- Are there other synchronous CPU-bound operations in the TTS or audio pipeline that should also be offloaded?