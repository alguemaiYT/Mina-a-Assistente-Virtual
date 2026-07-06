## 2024-07-06 - Initial analysis
**Learning:** `get_academic_context` launches a background thread for `sync_from_scraper` on EVERY text inference query.
**Action:** We need to throttle or debounce these synchronizations, otherwise we're spamming threads and local DB queries for no reason!

**Learning:** `_normalize_text` in `tts_client.py` uses multiple regex and string replacements that run for every single TTS synthesis call.
**Action:** Re-compiling regexes globally or using `lru_cache` speeds it up by ~100x.
