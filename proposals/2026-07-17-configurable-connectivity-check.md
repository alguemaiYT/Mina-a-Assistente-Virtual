# Configurable Connectivity Check

## Summary

Replace hardcoded external IP addresses (like `8.8.8.8`) used for connectivity checks with configuration-driven hostnames.

## Problem

The application currently performs connectivity checks to determine if it is online by attempting to connect to Google's public DNS server (`8.8.8.8:53`) in `main_gui.py` and potentially other files like `tts_api/main.py`. Hardcoding external network IPs is strictly forbidden by the project's requirements, as the application needs to support restricted or academic environments where specific external IPs may be blocked, routed differently, or not preferred.

## Evidence

In `main_gui.py`, around line 396:
```python
                        def ping():
                            try:
                                socket.setdefaulttimeout(1.5)
                                socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
                                return True
                            except Exception:
                                return False
```

In `tts_api/main.py`, around line 56:
```python
        s.connect(('8.8.8.8', 1))
```

## Proposed Solution

1. Move the configuration of the connectivity check host to the configuration manager (or environment variables).
2. Update the connectivity check logic to use this configuration value. A reasonable default, like `8.8.8.8` or a DNS lookup to a well-known reliable domain (e.g., `github.com`), can be provided in the configuration if no custom value is set, but it should be overridable.
3. In `main_gui.py`, fetch the host from the `cfg` object instead of hardcoding `8.8.8.8`.

## Benefits

- Adheres to project constraints and architectural guidelines regarding hardcoded IPs.
- Allows the application to work seamlessly in restricted or academic network environments with customized connectivity check targets.
- Increases the overall maintainability and flexibility of the application.

## Trade-offs

- Slightly increases the complexity of the configuration and the connectivity check logic.

## Risks

- Low risk. The change is primarily organizational and does not impact core functionality.
- Need to ensure a valid fallback host is provided if the configuration is missing or misconfigured.

## Estimated Complexity

- Low

## Priority

- High

## Success Criteria

- The application successfully performs connectivity checks using the configured host.
- No hardcoded `8.8.8.8` references remain in the codebase for connectivity purposes.
- The application correctly identifies its online/offline status based on the configured host.

## Open Questions

- What is the preferred configuration key for the connectivity check host (e.g., `SYSTEM_OPTIONS.NETWORK.CONNECTIVITY_CHECK_HOST`)?
- Should the default be an IP or a domain name?
