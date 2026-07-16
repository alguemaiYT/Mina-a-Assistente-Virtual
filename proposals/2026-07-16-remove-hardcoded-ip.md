# Remove Hardcoded External IP Checks

## Summary

Replace hardcoded references to `8.8.8.8` for network connectivity checks with dynamic, configuration-driven hostnames to ensure compatibility with restricted environments.

## Problem

The application currently uses a hardcoded IP address (`8.8.8.8`, Google's Public DNS) to check for network connectivity. In restricted or academic environments where external DNS queries to specific IPs are blocked or routed differently, this connectivity check will fail, leading to false negatives regarding network availability and potentially breaking functionality.

## Evidence

A search for `8.8.8.8` reveals its usage in the codebase:
- `main_gui.py` line 396: `socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))`
- `tts_api/main.py` line 56: `s.connect(('8.8.8.8', 1))`

## Proposed Solution

Replace the hardcoded `8.8.8.8` string with a configurable parameter. The application should load the hostname/IP from environment variables or configuration files, defaulting to a known reliable endpoint (like an internal gateway or a configurable external address) if no configuration is provided. Alternatively, use higher-level OS network status APIs if available, or simply attempt to connect to the actual API endpoint the application needs to use instead of an arbitrary third-party IP.

## Benefits

- Improved reliability in restricted network environments (e.g., academic, corporate).
- Avoids false negatives during network connectivity checks.
- Better alignment with standard enterprise configuration practices.

## Trade-offs

- Slightly increases configuration complexity by adding a new parameter.

## Risks

- Minor risk of breaking the check if the configured hostname is invalid or unresolvable.

## Estimated Complexity

- Low

## Priority

- Medium

## Success Criteria

- No hardcoded external IP addresses are present in the codebase for connectivity checks.
- Network checks pass successfully in restricted environments when configured appropriately.

## Open Questions

- What should be the default hostname/IP if none is provided in the configuration? Should it default to the API endpoint we actually want to connect to?