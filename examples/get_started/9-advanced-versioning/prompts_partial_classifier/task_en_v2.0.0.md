# Task Processor v2.0.0 (English)

English version 2.0.0.

**Important**: There is NO Russian version for v2.0.0!

When requesting `classifier={"lang": "ru"}`:
- System returns `task_ru_v1.0.0.md` (latest version WITH Russian)
- NOT v2.0.0 (which doesn't have Russian)

This demonstrates the "partial classifier coverage" behavior:
The system finds the latest version that HAS the requested classifier.
