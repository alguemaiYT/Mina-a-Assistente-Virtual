# Remove Hardcoded Network IPs for Ping/Connection Checks

## Summary

Replace hardcoded external IP addresses (e.g., `8.8.8.8`) used for internet connectivity checks and local IP resolution with configuration-driven or dynamic hostnames.

## Problem

The codebase currently contains hardcoded references to Google's public DNS server (`8.8.8.8`) to perform internet connectivity checks (`main_gui.py`) and local IP address resolution (`tts_api/main.py`). This creates brittleness in environments where external DNS is blocked, proxied, or routed differently (like strict corporate networks or air-gapped deployments).

## Evidence

- In `main_gui.py` around line 396: `socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))` is used to check internet connectivity.
- In `tts_api/main.py` around line 56: `s.connect(('8.8.8.8', 1))` is used to resolve the local host's IP address.
- The `AGENTS.md` strictly advises: "Recent efforts have removed hardcoded fallback IPs (e.g., in academic_db.py). Please avoid introducing hardcoded network addresses or paths."

## Proposed Solution

- Refactor `main_gui.py` to use a configurable list of hostnames/IPs for connectivity checks, defaulting to robust endpoints (e.g., standard root DNS, or an API health check endpoint). Ideally, use `ConfigManager` to allow users to override the ping check target.
- Refactor `tts_api/main.py` to use standard OS APIs for local IP resolution (e.g., `socket.gethostbyname(socket.gethostname())`) or connect to a locally guaranteed routable placeholder if OS APIs are insufficient, avoiding reliance on an external public IP just to find the local interface.

## Benefits

- **Reliability**: The application will function correctly in restricted networks that block traffic to `8.8.8.8`.
- **Maintainability**: Centralizes configuration, adhering to the project's architectural guidelines.
- **Security**: Reduces unexpected outbound traffic to third-party services.

## Trade-offs

- Slightly more complex logic for resolving the best available local IP if `socket.gethostname()` returns loopback (`127.0.0.1`) on certain misconfigured Linux systems.

## Risks

- Low risk. The network check logic is isolated and has a clear fallback mechanism already in place.

## Estimated Complexity

- Low

## Priority

- Medium

## Success Criteria

- All occurrences of `8.8.8.8` are removed from the source code.
- Internet connectivity checks pass on standard networks and gracefully fallback using configured endpoints.
- Local IP resolution in `tts_api/main.py` correctly identifies the LAN IP without contacting external servers.

## Open Questions

- Should the internet connectivity check endpoint be user-configurable via the GUI Settings window, or just in `.env`/config files?