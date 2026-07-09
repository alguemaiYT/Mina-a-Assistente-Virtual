# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased] - 2026-07-07

### Added
- Repository improvements: analysis, CI/CD, and development infrastructure (6cd1e38)
- Test: Add test_live_sensitivity.py to diagnose real-time KWS sensitivity settings (ffe15fd)

### Changed
- Bolt: Optimize TTS normalization and DB sync logic (7badd4f)
- Address code review feedback: add logging to load/save, fix color detection case sensitivity and type inference for color values (5663702)
- Apply suggestions from code review (db36d2c)
- Fix code review issues: correct QML text animation and emotion sizing calculation (fa1461d)
- Use descriptive QML layout helper name (ca417ca)

### Fixed
- Debounce canvas drag/resize I/O — persist only on mouse release (ec83c00)
- Remove hardcoded fallback IP 10.129.75.230 in academic_db.py (752bd0b)

### Removed / Chore
- Complete repository hygiene and untrack academic.db and memory.db databases (752bd0b)
- Add config/*.db to .gitignore (752bd0b)
- Delete README-cn.md (752bd0b)
- Remove unused `__future__` annotations import (4ddf164)
- Remove unused `QWidget` import in `wake_word_widget.py` (5def4f4)
- Remove unused 'annotations' import from resource_finder.py (2195e03)
