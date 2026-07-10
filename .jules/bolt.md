## 2024-07-10 - Reusing HTTP Sessions for Real-Time TTS

**Learning:** The codebase repeatedly creates an `aiohttp.ClientSession` for each audio chunk request during real-time TTS. This adds significant overhead (TCP and TLS handshake latency) to each synthesis request, which severely impacts response times for small audio chunks.

**Action:** Reuse a single `aiohttp.ClientSession` across multiple requests by initializing it in the client instance and tearing it down only when the client is closed.
