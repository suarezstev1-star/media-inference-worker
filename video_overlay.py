#!/usr/bin/env python3
"""Compose brand text / CTA over generated videos.

The bundled static ffmpeg has no drawtext (no libfreetype), so text is
rendered to transparent PNGs with PIL (full Spanish + brand fonts) and
composited with ffmpeg's overlay filter. Reusable for the hero and for the
product commercials.
"""

import subprocess
import tempfile
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw

import overlay as ov  # brand system: colors, fonts, helpers, PHONE, WORDMARK

FF = imageio_ffmpeg.get_ffmpeg_exe()
OUT = Path(__file__).with_name("output")


def _draw_lines(d, lines, f, cx, y, color, gap, shadow=True):
    for ln in lines:
        w = ov.text_w(d, ln, f)
        x = cx - w // 2
        if shadow:
            d.text((x + 3, y + 3), ln, font=f, fill=(0, 0, 0, 180))
        d.text((x, y), ln, font=f, fill=color)
        a, de = f.getmetrics()
        y += a + de + gap
    return y


def scrim_png(size):
    """Persistent bottom navy gradient for legibility."""
    W, H = size
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    start = int(H * 0.52)
    px = img.load()
    for yy in range(start, H):
        t = (yy - start) / (H - start)
        a = int(200 * (t ** 1.3))
        for xx in range(W):
            px[xx, yy] = (*ov.NAVY, a)
    return img


def wordmark_png(size):
    W, H = size
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = ov.font(ov.SANS_B, int(W * 0.026))
    w = ov.text_w(d, ov.WORDMARK, f)
    d.text(((W - w) // 2, H - int(H * 0.06)), ov.WORDMARK, font=f, fill=ov.GOLD_SOFT)
    return img


def text_beat_png(size, lines, font_path, fsize_frac, color, y_frac):
    W, H = size
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = ov.font(font_path, int(W * fsize_frac))
    _draw_lines(d, lines, f, W // 2, int(H * y_frac), color, int(W * 0.014))
    return img


def cta_beat_png(size, y_frac=0.70, label=None):
    W, H = size
    label = label or f"Llama hoy:  {ov.PHONE}"
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = ov.font(ov.SANS_B, int(W * 0.050))
    w = ov.text_w(d, label, f)
    pad_x, pad_y = int(W * 0.06), int(W * 0.035)
    pill_w = w + pad_x * 2
    a, de = f.getmetrics()
    pill_h = a + de + pad_y * 2
    x0 = (W - pill_w) // 2
    y0 = int(H * y_frac)
    d.rounded_rectangle([x0, y0, x0 + pill_w, y0 + pill_h],
                        radius=pill_h // 2, fill=ov.GOLD)
    d.text((x0 + pad_x, y0 + pad_y), label, font=f, fill=ov.NAVY)
    return img


def compose(src, out, layers, target=(1080, 1920)):
    """layers: list of dicts {img: PIL.Image, start: float|None, end: float|None}."""
    tmp = Path(tempfile.mkdtemp())
    paths = []
    for i, L in enumerate(layers):
        p = tmp / f"L{i}.png"
        L["img"].save(p)
        paths.append(p)

    inputs = ["-i", str(src)]
    for p in paths:
        inputs += ["-i", str(p)]

    W, Ht = target
    chain = (f"[0:v]scale={W}:{Ht}:force_original_aspect_ratio=increase,"
             f"crop={W}:{Ht}[base]")
    parts = [chain]
    cur = "base"
    for i, L in enumerate(layers):
        nxt = f"v{i}"
        en = ""
        if L.get("start") is not None:
            en = f":enable='between(t,{L['start']},{L['end']})'"
        parts.append(f"[{cur}][{i+1}:v]overlay=0:0{en}[{nxt}]")
        cur = nxt
    fc = ";".join(parts)

    OUT_FINAL = OUT / "final"
    OUT_FINAL.mkdir(parents=True, exist_ok=True)
    dest = OUT_FINAL / out
    cmd = [FF, "-y", *inputs, "-filter_complex", fc, "-map", f"[{cur}]",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
           "-an", str(dest)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-1500:])
        raise SystemExit(f"ffmpeg failed for {out}")
    print("saved", dest)
    return dest


def build_hero(src="hero_video_veo.mp4", out="hero_video.mp4", size=(1080, 1920)):
    layers = [
        {"img": scrim_png(size), "start": None, "end": None},
        {"img": text_beat_png(size, ["Un funeral hoy", "cuesta $8,000+"],
                              ov.SERIF, 0.070, ov.WHITE, 0.60),
         "start": 0.2, "end": 2.5},
        {"img": text_beat_png(size, ["Deja un legado,", "no una deuda."],
                              ov.SERIF, 0.078, ov.GOLD, 0.60),
         "start": 2.5, "end": 4.3},
        {"img": cta_beat_png(size, 0.66), "start": 4.3, "end": 99},
        {"img": wordmark_png(size), "start": None, "end": None},
    ]
    compose(OUT / src, out, layers, size)


def build_product(src="prod_llamada_veo.mp4", out="comercial_llamada.mp4",
                  size=(1080, 1920)):
    layers = [
        {"img": scrim_png(size), "start": None, "end": None},
        {"img": text_beat_png(size, ["¿Y si lo resolvieras", "todo en una llamada?"],
                              ov.SERIF, 0.066, ov.WHITE, 0.58),
         "start": 0.2, "end": 2.4},
        {"img": text_beat_png(size, ["Vida · Gastos finales", "· Ahorro"],
                              ov.SERIF, 0.072, ov.GOLD, 0.60),
         "start": 2.4, "end": 4.2},
        {"img": cta_beat_png(size, 0.66), "start": 4.2, "end": 99},
        {"img": wordmark_png(size), "start": None, "end": None},
    ]
    compose(OUT / src, out, layers, size)


def build_vida(src="prod_vida_veo.mp4", out="comercial_vida.mp4",
               size=(1080, 1920)):
    layers = [
        {"img": scrim_png(size), "start": None, "end": None},
        {"img": text_beat_png(size, ["Tu vida vale.", "Tu familia también."],
                              ov.SERIF, 0.070, ov.WHITE, 0.58),
         "start": 0.2, "end": 2.4},
        {"img": text_beat_png(size, ["Vida entera:", "protección de por vida"],
                              ov.SERIF, 0.066, ov.GOLD, 0.60),
         "start": 2.4, "end": 4.2},
        {"img": cta_beat_png(size, 0.66), "start": 4.2, "end": 99},
        {"img": wordmark_png(size), "start": None, "end": None},
    ]
    compose(OUT / src, out, layers, size)


def build_iul(src="prod_iul_veo.mp4", out="comercial_iul.mp4",
              size=(1080, 1920)):
    layers = [
        {"img": scrim_png(size), "start": None, "end": None},
        {"img": text_beat_png(size, ["¿Y si tu seguro", "también te diera ahorro?"],
                              ov.SERIF, 0.060, ov.WHITE, 0.58),
         "start": 0.2, "end": 2.6},
        {"img": text_beat_png(size, ["Protección de vida", "+ ahorro para tu retiro"],
                              ov.SERIF, 0.060, ov.GOLD, 0.60),
         "start": 2.6, "end": 4.3},
        {"img": cta_beat_png(size, 0.66), "start": 4.3, "end": 99},
        {"img": wordmark_png(size), "start": None, "end": None},
    ]
    compose(OUT / src, out, layers, size)


if __name__ == "__main__":
    import sys
    builders = {"product": build_product, "vida": build_vida, "iul": build_iul}
    builders.get(sys.argv[1] if len(sys.argv) > 1 else "", build_hero)()
