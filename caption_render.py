#!/usr/bin/env python3
"""Modern synced captions (Reels/TikTok style) over a video, plus the VO.

Reads a per-sentence timing JSON ([{text,start,end}]) produced by kokoro_tts.py
and renders bottom-third bold captions that pop in when spoken, keywords in
gold, on a soft dark pill. Stretches the video to the voiceover length so
motion stays continuous, then muxes the VO.

    python caption_render.py SRC_VIDEO VO_WAV TIMING_JSON OUT [CTA_PHONE]
"""

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw

import overlay as ov
import video_overlay as vo2

FF = imageio_ffmpeg.get_ffmpeg_exe()

HIGHLIGHT = re.compile(r"^[¡¿]?(\$?\d[\d.,]*|mil|dólares|gratis|hoy|ahora|Dinastía|"
                       r"nunca|todo|vida|familia|llama|ya)[\.,!?…]?$", re.IGNORECASE)


def dur(path):
    r = subprocess.run([FF, "-i", str(path)], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", r.stderr)
    return int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]) if m else None


def wrap_words(draw, words, f, max_w):
    lines, cur = [], []
    for w in words:
        test = " ".join(cur + [w])
        if ov.text_w(draw, test, f) <= max_w or not cur:
            cur.append(w)
        else:
            lines.append(cur); cur = [w]
    if cur:
        lines.append(cur)
    return lines


def caption_png(size, text):
    W, H = size
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = ov.font(ov.SANS_B, int(W * 0.062))
    max_w = int(W * 0.84)
    lines = wrap_words(d, text.split(), f, max_w)
    asc, desc = f.getmetrics()
    lh = asc + desc + int(W * 0.012)
    block_h = lh * len(lines)
    y0 = int(H * 0.66) - block_h // 2

    # soft dark pill behind the whole block
    pad = int(W * 0.035)
    widths = [ov.text_w(d, " ".join(ln), f) for ln in lines]
    bw = max(widths) + pad * 2
    x0 = (W - bw) // 2
    d.rounded_rectangle([x0, y0 - pad, x0 + bw, y0 + block_h + pad // 2],
                        radius=int(W * 0.03), fill=(8, 18, 36, 165))

    y = y0
    for ln in lines:
        lw = ov.text_w(d, " ".join(ln), f)
        x = (W - lw) // 2
        for w in ln:
            color = ov.GOLD if HIGHLIGHT.match(w) else ov.WHITE
            d.text((x + 2, y + 2), w, font=f, fill=(0, 0, 0, 180))
            d.text((x, y), w, font=f, fill=color)
            x += ov.text_w(d, w + " ", f)
        y += lh
    return img


def main():
    src, wav, tj, out = sys.argv[1:5]
    phone = sys.argv[5] if len(sys.argv) > 5 else ov.PHONE
    size = (1080, 1920)
    timing = json.load(open(tj))
    vdur = dur(src) or 6.0
    adur = dur(wav) or 6.0
    total = adur + 0.5

    layers = [{"img": vo2.scrim_png(size), "start": None, "end": None}]
    for seg in timing:
        layers.append({"img": caption_png(size, seg["text"]),
                       "start": round(seg["start"], 2), "end": round(seg["end"] + 0.15, 2)})
    # CTA appears with the final line and holds to the end
    layers.append({"img": vo2.cta_beat_png(size, 0.80, label=f"Llama hoy:  {phone}"),
                   "start": round(timing[-1]["start"], 2), "end": 999})
    layers.append({"img": vo2.wordmark_png(size), "start": None, "end": None})

    tmp = Path(tempfile.mkdtemp())
    paths = []
    for i, L in enumerate(layers):
        p = tmp / f"L{i}.png"; L["img"].save(p); paths.append(p)

    inputs = ["-i", src, "-i", wav]
    for p in paths:
        inputs += ["-i", str(p)]

    W, H = size
    factor = min(total / vdur, 2.2)
    base = f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setpts={factor:.4f}*PTS[bg]"
    parts = [base]
    cur = "bg"
    for i, L in enumerate(layers):
        en = f":enable='between(t,{L['start']},{L['end']})'" if L.get("start") is not None else ""
        parts.append(f"[{cur}][{i+3}:v]overlay=0:0{en}[v{i}]")
        cur = f"v{i}"
    parts.append(f"[1:a]afade=t=out:st={max(0,adur-0.4):.2f}:d=0.4[a]")
    fc = ";".join(parts)

    cmd = [FF, "-y", *inputs, "-filter_complex", fc, "-map", f"[{cur}]", "-map", "[a]",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
           "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.2f}", out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-1800:]); return 1
    print("saved", out, f"({total:.1f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
