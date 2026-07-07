with open("src/utils/academic_db.py", "r") as f:
    content = f.read()

content = content.replace("def init_db():", "\n\ndef init_db():")
content = content.replace("def save_professor", "\n\ndef save_professor")
content = content.replace("def save_schedule", "\n\ndef save_schedule")
content = content.replace("def save_news_event", "\n\ndef save_news_event")
content = content.replace("def clear_schedules", "\n\ndef clear_schedules")
content = content.replace("def get_professors", "\n\ndef get_professors")
content = content.replace("def get_recent_news_events", "\n\ndef get_recent_news_events")
content = content.replace("def get_active_classes", "\n\ndef get_active_classes")
content = content.replace("def get_upcoming_classes_today", "\n\ndef get_upcoming_classes_today")
content = content.replace("def sync_from_scraper", "\n\ndef sync_from_scraper")
content = content.replace("def get_academic_context", "\n\ndef get_academic_context")

import re
content = re.sub(r'\n{4,}', '\n\n\n', content)

# fix the global scope in get_academic_context
old_code = """    global _last_sync_time, _sync_lock
    # Fire off database synchronization in the background, max once per 60 seconds
    if not _sync_lock and time.time() - _last_sync_time > 60:
        _sync_lock = True

        def _sync_worker():
            global _last_sync_time, _sync_lock"""

new_code = """    global _sync_lock
    # Fire off database synchronization in the background, max once per 60 seconds
    if not _sync_lock and time.time() - _last_sync_time > 60:
        _sync_lock = True

        def _sync_worker():
            global _last_sync_time, _sync_lock"""

content = content.replace(old_code, new_code)

with open("src/utils/academic_db.py", "w") as f:
    f.write(content)
