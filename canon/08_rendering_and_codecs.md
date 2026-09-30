# 08 — Rendering and codecs

**Status: CANON transport principle.**

The canonical transport is the Latin token sequence.

Alternative encodings may exist:

```text
Latin surface
Sitelen Pona profile
voice/token recognition
UI gestures
```

All must resolve to the same canonical token IDs before semantic processing.

Encoding is therefore treated as:

```text
physical representation → token IDs → parse/bind → semantic operation
```

Ambiguous recognition must produce uncertainty rather than an executable guess.

This repository intentionally contains no font files and does not define a final glyph standard.
