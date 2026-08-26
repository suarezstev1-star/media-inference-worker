#!/usr/bin/env python3
"""Compose crisp Spanish ad copy over the AI-generated brand backgrounds.

AI image models render text unreliably (wrong accents, garbled phone
numbers), so all headlines, CTAs and the phone number are drawn here with
real fonts. Reads backgrounds from output/ and writes finished JPEGs (never
PNG — TikTok rejects PNG) to output/final/.
"""

import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).with_name("output")
FINAL = OUT / "final"

# --- Brand system -----------------------------------------------------------
NAVY = (11, 31, 58)
GOLD = (206, 170, 90)
GOLD_SOFT = (223, 197, 138)
CREAM = (245, 239, 227)
WHITE = (250, 248, 244)

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

PHONE = "(407) 375-1344"
WORDMARK = "DINASTÍA  ·  INSURANCE SOLUTIONS"


def font(path, size):
    return ImageFont.truetype(path, size)


def text_w(draw, s, f):
    b = draw.textbbox((0, 0), s, font=f)
    return b[2] - b[0]


def wrap(draw, s, f, max_w):
    words = s.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if text_w(draw, t, f) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_block(draw, lines, f, x, y, color, line_gap, align="left", box_w=None,
               shadow=True):
    for ln in lines:
        w = text_w(draw, ln, f)
        if align == "center":
            lx = x + (box_w - w) // 2
        elif align == "right":
            lx = x + box_w - w
        else:
            lx = x
        if shadow:
            draw.text((lx + 2, y + 2), ln, font=f, fill=(0, 0, 0, 160))
        draw.text((lx, y), ln, font=f, fill=color)
        asc, desc = f.getmetrics()
        y += asc + desc + line_gap
    return y


def bottom_scrim(img, frac=0.55, strength=210):
    """Darken the lower part of a photo so text stays readable."""
    w, h = img.size
    grad = Image.new("L", (1, h), 0)
    start = int(h * (1 - frac))
    for yy in range(start, h):
        t = (yy - start) / max(1, (h - start))
        grad.putpixel((0, yy), int(strength * (t ** 1.4)))
    grad = grad.resize((w, h))
    black = Image.new("RGB", (w, h), NAVY)
    return Image.composite(black, img, grad)


def fit_bg(name, size):
    src = Image.open(OUT / f"{name}.png").convert("RGB")
    tw, th = size
    sw, sh = src.size
    scale = max(tw / sw, th / sh)
    src = src.resize((int(sw * scale), int(sh * scale)), Image.LANCZOS)
    sw, sh = src.size
    left, top = (sw - tw) // 2, (sh - th) // 2
    return src.crop((left, top, left + tw, top + th))


def cta_pill(draw, cx, y, size, label=f"Llama hoy:  {PHONE}"):
    f = font(SANS_B, int(size[0] * 0.042))
    pad_x, pad_y = int(size[0] * 0.05), int(size[0] * 0.028)
    w = text_w(draw, label, f)
    pill_w, pill_h = w + pad_x * 2, (f.getmetrics()[0] + f.getmetrics()[1]) + pad_y * 2
    x0 = cx - pill_w // 2
    draw.rounded_rectangle([x0, y, x0 + pill_w, y + pill_h],
                           radius=pill_h // 2, fill=GOLD)
    draw.text((x0 + pad_x, y + pad_y), label, font=f, fill=NAVY)
    return y + pill_h


def wordmark(draw, size, y=None):
    f = font(SANS_B, int(size[0] * 0.026))
    w = text_w(draw, WORDMARK, f)
    if y is None:
        y = size[1] - int(size[1] * 0.055)
    draw.text(((size[0] - w) // 2, y), WORDMARK, font=f, fill=GOLD_SOFT)


def accent_line(draw, cx, y, size, w_frac=0.16):
    w = int(size[0] * w_frac)
    draw.rectangle([cx - w // 2, y, cx + w // 2, y + max(3, int(size[0] * 0.006))],
                   fill=GOLD)


# --- Pieces -----------------------------------------------------------------

def piece_photo(bg, size, eyebrow, headline, sub, cta=True, out=None):
    """Photo bg, text anchored to the bottom over a scrim."""
    img = fit_bg(bg, size)
    img = bottom_scrim(img, frac=0.62, strength=225)
    d = ImageDraw.Draw(img)
    W, H = size
    m = int(W * 0.08)
    box_w = W - 2 * m
    hf = font(SERIF, int(W * 0.072))
    ef = font(SANS_B, int(W * 0.032))
    sf = font(SANS, int(W * 0.038))

    hlines = wrap(d, headline, hf, box_w)
    slines = wrap(d, sub, sf, box_w) if sub else []
    # measure total height to anchor from bottom
    def block_h(lines, f, gap):
        a, de = f.getmetrics()
        return len(lines) * (a + de + gap)
    total = block_h([eyebrow], ef, int(W*0.01)) + int(W*0.03) \
        + block_h(hlines, hf, int(W*0.012)) + (int(W*0.02) + block_h(slines, sf, int(W*0.01)) if slines else 0)
    if cta:
        total += int(W * 0.14)
    y = H - int(H * 0.10) - total

    y = draw_block(d, [eyebrow.upper()], ef, m, y, GOLD_SOFT, int(W*0.01))
    accent_line(d, m + int(box_w*0.0), y - int(W*0.005), size, 0.14) if False else None
    y += int(W * 0.015)
    y = draw_block(d, hlines, hf, m, y, WHITE, int(W*0.012))
    if slines:
        y += int(W * 0.015)
        y = draw_block(d, slines, sf, m, y, CREAM, int(W*0.01))
    if cta:
        y += int(W * 0.03)
        cta_pill(d, W // 2, y, size)
    wordmark(d, size)
    save(img, out)


def piece_card(bg, size, eyebrow, headline, sub=None, checklist=None,
               big=None, cta=True, out=None):
    """Navy card, centered stack that auto-scales to never overflow.

    The CTA pill and wordmark live in a reserved bottom band; the content
    stack is laid out above it and shrunk until it fits.
    """
    img = fit_bg(bg, size)
    d = ImageDraw.Draw(img)
    W, H = size
    m = int(W * 0.10)
    box_w = W - 2 * m
    top_start = int(H * 0.12)
    bottom_band = int(H * (0.20 if cta else 0.10))
    avail = (H - bottom_band) - top_start

    def build(scale):
        """Return a list of draw ops and the total stack height."""
        ops, y = [], 0
        ef = font(SANS_B, int(W * 0.034 * scale))
        hf = font(SERIF, int(W * 0.075 * scale))
        sf = font(SANS, int(W * 0.040 * scale))
        cf = font(SANS_B, int(W * 0.044 * scale))
        bf = font(SERIF, int(W * 0.20 * scale))

        def add(lines, f, color, gap, hang=0):
            nonlocal y
            for ln in lines:
                ops.append((ln, f, color, y, hang))
                a, de = f.getmetrics()
                y += a + de + gap

        add([eyebrow.upper()], ef, GOLD_SOFT, int(W * 0.02))
        ops.append(("__accent__", None, None, y, 0))
        y += int(W * 0.05)
        if big:
            add([big], bf, GOLD, int(W * 0.02))
        add(wrap(d, headline, hf, box_w), hf, WHITE, int(W * 0.012 * scale))
        if sub:
            y += int(W * 0.02)
            add(wrap(d, sub, sf, box_w), sf, CREAM, int(W * 0.012 * scale))
        if checklist:
            y += int(W * 0.03)
            hang = text_w(d, "✓  ", cf)
            for item in checklist:
                lines = wrap(d, f"✓  {item}", cf, box_w)
                for i, ln in enumerate(lines):
                    add([ln], cf, CREAM, int(W * 0.012 * scale),
                        hang=0 if i == 0 else hang)
                y += int(W * 0.018)
        return ops, y

    scale = 1.0
    for _ in range(8):
        ops, total = build(scale)
        if total <= avail:
            break
        scale *= 0.92

    y0 = top_start + max(0, (avail - total) // 2)
    for ln, f, color, dy, hang in ops:
        if ln == "__accent__":
            accent_line(d, W // 2, y0 + dy, size)
            continue
        w = text_w(d, ln, f)
        if hang > 0 or ln.startswith("✓"):
            lx = m + hang          # checklist: left-aligned block
        else:
            lx = m + (box_w - w) // 2   # everything else: centered
        d.text((lx, y0 + dy), ln, font=f, fill=color)
        if ln.startswith("✓"):
            d.text((lx, y0 + dy), "✓", font=f, fill=GOLD)

    if cta:
        cta_pill(d, W // 2, H - bottom_band + int(H * 0.03), size)
    wordmark(d, size)
    save(img, out)


def piece_brand(bg, size, tagline, out=None):
    """Emblem on top, tagline + CTA in a solid navy footer band below it."""
    img = fit_bg(bg, size)
    d = ImageDraw.Draw(img)
    W, H = size
    m = int(W * 0.09)
    box_w = W - 2 * m
    band_top = int(H * 0.57)
    d.rectangle([0, band_top, W, H], fill=NAVY)
    d.rectangle([0, band_top, W, band_top + max(3, int(H * 0.005))], fill=GOLD)

    hf = font(SERIF, int(W * 0.058))
    lines = wrap(d, tagline, hf, box_w)
    a, de = hf.getmetrics()
    gap = int(W * 0.012)
    y = band_top + int(H * 0.05)
    draw_block(d, lines, hf, m, y, WHITE, gap, "center", box_w, shadow=False)
    y += len(lines) * (a + de + gap) + int(H * 0.03)
    cta_pill(d, W // 2, y, size)
    wordmark(d, size)
    save(img, out)


def save(img, out):
    FINAL.mkdir(parents=True, exist_ok=True)
    dest = FINAL / f"{out}.jpg"
    img.convert("RGB").save(dest, "JPEG", quality=92)
    print("saved", dest)


def main():
    # ---- Organic educational series (9:16) ----
    S = (1080, 1920)
    piece_card("fondo_navy_a", S, "Gastos finales · Dato 1",
               "Un funeral hoy cuesta entre $8,000 y $12,000.",
               sub="¿Tu familia sabría de dónde sacarlo?", cta=False,
               out="serie_1_costo")
    piece_card("fondo_navy_b", S, "Gastos finales · Dato 2",
               "“Aceptación garantizada” no siempre significa lo que crees.",
               sub="Pregunta si hay examen médico y periodo de espera antes de firmar.",
               cta=False, out="serie_2_letra_chica")
    piece_card("fondo_navy_c", S, "Gastos finales · Dato 3",
               "El GoFundMe no es un plan.",
               sub="Las colectas fallan en el peor momento. Un plan se decide antes.",
               cta=False, out="serie_3_gofundme")
    piece_card("fondo_navy_a", S, "Gastos finales · Dato 4",
               "3 mitos que te cuestan tranquilidad.",
               checklist=["“Soy muy mayor” — hay planes 50–85.",
                          "“Mi salud lo impide” — hay opciones sin examen.",
                          "“Es muy caro” — tarifa fija desde poco al mes."],
               cta=False, out="serie_4_mitos")
    piece_card("fondo_navy_b", S, "Gastos finales · Dato 5",
               "¿Vida entera o término?",
               sub="Para gastos finales, la vida entera mantiene tu tarifa fija de por vida. Te explico tu caso en 5 minutos.",
               cta=True, out="serie_5_vida_entera")

    # ---- Sales / lead-gen pack ----
    piece_photo("fondo_familia_45", (1080, 1350), "Dinastía Insurance Solutions",
                "Deja un legado, no una deuda.",
                "Cobertura de gastos finales con tarifa fija de por vida.",
                out="ventas_1_hero")
    piece_card("fondo_navy_11", (1080, 1080), "La pregunta que evitamos",
               "¿Quién pagaría tu funeral hoy?",
               big="$8,000+", sub="Deja ese peso resuelto en una sola llamada.",
               out="ventas_2_costo")
    piece_card("fondo_navy_11b", (1080, 1080), "Tu cobertura incluye",
               "Simple, digno y a tu alcance.",
               checklist=["Sin examen médico en planes elegibles",
                          "Tarifa fija de por vida",
                          "Beneficio libre de impuestos para tu familia",
                          "Se resuelve en una llamada"],
               out="ventas_3_beneficios")
    piece_brand("fondo_emblema_11", (1080, 1080),
                "Protege a los tuyos como lo que eres: su fortaleza.",
                out="ventas_4_marca")
    piece_photo("fondo_manos_45", (1080, 1350), "Gastos finales",
                "El último regalo es la tranquilidad.",
                "Que despedirte no le cueste una deuda a quien amas.",
                out="ventas_5_legado")
    piece_photo("fondo_familia_11", (1080, 1080), "Atención en español",
                "Hablemos claro, sin letra chica.",
                "Te explico tus opciones sin compromiso.",
                out="ventas_6_confianza")

    print("\nDONE ->", FINAL)


if __name__ == "__main__":
    main()
