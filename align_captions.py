#!/usr/bin/env python3
"""Word-align a naturally-spoken VO and group it into short caption phrases.

Runs faster-whisper on the (single-pass, natural) voiceover to get word
timestamps, then groups words into ~3-word caption lines that break on
punctuation. Writes a timing JSON [{text,start,end}] for caption_render.py.

    python align_captions.py VO_WAV OUT_JSON [max_words] [max_secs]
"""

import json
import re
import sys

from faster_whisper import WhisperModel

wav = sys.argv[1]
out = sys.argv[2]
MAX_W = int(sys.argv[3]) if len(sys.argv) > 3 else 3
MAX_S = float(sys.argv[4]) if len(sys.argv) > 4 else 1.7

model = WhisperModel("small", device="cpu", compute_type="int8")
segments, _ = model.transcribe(wav, language="es", word_timestamps=True, beam_size=5)

words = []
for s in segments:
    for w in (s.words or []):
        t = w.word.strip()
        if t:
            words.append((t, w.start, w.end))

caps, cur, start = [], [], None
for i, (t, ws, we) in enumerate(words):
    if start is None:
        start = ws
    cur.append(t)
    ends_punct = bool(re.search(r"[\.!?…,:]$", t))
    long_enough = len(cur) >= MAX_W or (we - start) >= MAX_S
    if ends_punct or long_enough or i == len(words) - 1:
        caps.append({"text": " ".join(cur), "start": round(start, 3), "end": round(we, 3)})
        cur, start = [], None

json.dump(caps, open(out, "w"), ensure_ascii=False, indent=1)
print(f"wrote {out} | {len(caps)} captions from {len(words)} words")
