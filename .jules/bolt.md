## 2024-05-19 - Removed redundant DB schema queries

**Learning:** `init_db()` containing `CREATE TABLE IF NOT EXISTS` queries in `academic_db.py` and `memory_db.py` were called prior to *every* data access or save operation (100+ times during syncs/loops). While SQLite caching makes this fast, avoiding it completely using a module-level `_db_initialized` boolean bypasses the unnecessary I/O overhead entirely (0.0450s -> 0.0009s per 100 calls).

**Action:** Look for high-frequency database accesses or init calls and guard them with an initialized state flag in memory.

## 2024-05-19 - Removed __import__ inside inner loops
**Learning:** Found an inline `__import__('json').loads()` inside the `chat_bridge` stream parser. Although it was probably used initially as a quick fix, `__import__` has measurable overhead compared to utilizing a globally imported module, especially in an ultra-high-frequency token processing loop.

**Action:** Standardize module imports globally instead of localized dynamic imports in hot loops.
