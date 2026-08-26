#!/usr/bin/env python3
"""Render the month's Dinastía social pack: single posts + carousels.

Reuses the brand system from overlay.py. Single posts reuse piece_card /
piece_photo; carousels add progress dots, a "Desliza →" hint and a
myth/fact (mito/realidad) layout. Outputs JPEGs to output/social/.
"""

from pathlib import Path
from PIL import Image, ImageDraw

import overlay as ov

SOC = ov.OUT / "social"
GOLD, NAVY, WHITE, CREAM, GOLD_SOFT = ov.GOLD, ov.NAVY, ov.WHITE, ov.CREAM, ov.GOLD_SOFT


def save(img, name):
    SOC.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(SOC / f"{name}.jpg", "JPEG", quality=92)
    print("saved", name)


def dots(d, size, n, active):
    W, H = size
    r = int(W * 0.010)
    gap = int(W * 0.035)
    total = n * (2 * r) + (n - 1) * (gap - 2 * r)
    x = (W - total) // 2 + r
    y = int(H * 0.07)
    for i in range(n):
        c = GOLD if i == active else (120, 130, 150)
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
        x += gap


def swipe(d, size):
    W, H = size
    f = ov.font(ov.SANS_B, int(W * 0.040))
    t = "Desliza  →"
    w = ov.text_w(d, t, f)
    d.text((W - w - int(W * 0.08), int(H * 0.88)), t, font=f, fill=GOLD_SOFT)


def wm(d, size):
    W, H = size
    f = ov.font(ov.SANS_B, int(W * 0.026))
    w = ov.text_w(d, ov.WORDMARK, f)
    d.text(((W - w) // 2, H - int(H * 0.055)), ov.WORDMARK, font=f, fill=GOLD_SOFT)


# ---------- carousel slides (4:5) ----------
SZ = (1080, 1350)


def car_cover(bg, kicker, title, n, out):
    img = ov.fit_bg(bg, SZ); d = ImageDraw.Draw(img)
    W, H = SZ; m = int(W * 0.10)
    dots(d, SZ, n, 0)
    ef = ov.font(ov.SANS_B, int(W * 0.036))
    kw = ov.text_w(d, kicker.upper(), ef)
    d.text(((W - kw) // 2, int(H * 0.30)), kicker.upper(), font=ef, fill=GOLD_SOFT)
    y = int(H * 0.37)
    hf = ov.font(ov.SERIF, int(W * 0.095))
    for ln in ov.wrap(d, title, hf, W - 2 * m):
        lw = ov.text_w(d, ln, hf); d.text(((W - lw) // 2, y), ln, font=hf, fill=WHITE)
        y += int(W * 0.11)
    ov.accent_line(d, W // 2, int(H * 0.30) - int(W * 0.02), SZ)
    swipe(d, SZ); wm(d, SZ)
    save(img, out)


def car_mf(bg, idx, n, mito, realidad, out):
    img = ov.fit_bg(bg, SZ); d = ImageDraw.Draw(img)
    W, H = SZ; m = int(W * 0.10); box = W - 2 * m
    dots(d, SZ, n, idx)
    y = int(H * 0.24)
    lf = ov.font(ov.SANS_B, int(W * 0.040))
    d.text((m, y), "MITO", font=lf, fill=(200, 120, 120)); y += int(W * 0.07)
    mf = ov.font(ov.SERIF, int(W * 0.058))
    for ln in ov.wrap(d, mito, mf, box):
        d.text((m, y), ln, font=mf, fill=WHITE); y += int(W * 0.075)
    y += int(W * 0.05)
    d.text((m, y), "REALIDAD", font=lf, fill=GOLD); y += int(W * 0.07)
    rf = ov.font(ov.SANS, int(W * 0.048))
    for ln in ov.wrap(d, realidad, rf, box):
        d.text((m, y), ln, font=rf, fill=CREAM); y += int(W * 0.065)
    wm(d, SZ)
    save(img, out)


def car_body(bg, idx, n, label, main, sub, out):
    img = ov.fit_bg(bg, SZ); d = ImageDraw.Draw(img)
    W, H = SZ; m = int(W * 0.10); box = W - 2 * m
    dots(d, SZ, n, idx)
    y = int(H * 0.26)
    if label:
        lf = ov.font(ov.SANS_B, int(W * 0.038))
        d.text((m, y), label.upper(), font=lf, fill=GOLD_SOFT); y += int(W * 0.075)
    hf = ov.font(ov.SERIF, int(W * 0.066))
    for ln in ov.wrap(d, main, hf, box):
        d.text((m, y), ln, font=hf, fill=WHITE); y += int(W * 0.082)
    if sub:
        y += int(W * 0.03)
        sf = ov.font(ov.SANS, int(W * 0.046))
        for ln in ov.wrap(d, sub, sf, box):
            d.text((m, y), ln, font=sf, fill=CREAM); y += int(W * 0.062)
    wm(d, SZ)
    save(img, out)


def car_cta(bg, idx, n, title, out):
    img = ov.fit_bg(bg, SZ); d = ImageDraw.Draw(img)
    W, H = SZ; m = int(W * 0.10)
    dots(d, SZ, n, idx)
    y = int(H * 0.34)
    hf = ov.font(ov.SERIF, int(W * 0.080))
    for ln in ov.wrap(d, title, hf, W - 2 * m):
        lw = ov.text_w(d, ln, hf); d.text(((W - lw) // 2, y), ln, font=hf, fill=WHITE)
        y += int(W * 0.095)
    y += int(W * 0.05)
    ov.cta_pill(d, W // 2, y, SZ)
    wm(d, SZ)
    save(img, out)


def main():
    # ---------------- SINGLE POSTS ----------------
    P45, P11 = (1080, 1350), (1080, 1080)
    # Week 1
    ov.piece_card.__wrapped__ if False else None
    _card("soc_navy_45_a", P45, "Gastos finales", "Un funeral cuesta hasta $12,000.",
          sub="¿Tu familia sabría de dónde sacarlo? Nosotros te ayudamos.", cta=True, out="s1_lun_costo")
    _photo("fondo_manos_45", P45, "Gastos finales", "El último regalo es la tranquilidad.",
           "Deja un legado, no una deuda.", out="s1_vie_legado")
    _card("soc_navy_11_a", P11, "Cuéntanos", "¿Ya tienes un plan para tus gastos finales?",
          sub="Responde 👇 y te orientamos sin compromiso.", cta=False, out="s1_dom_pregunta")
    # Week 2
    _card("soc_navy_45_b", P45, "Vida entera", "Protección de por vida, tarifa que no sube.",
          sub="Simple, digno y a tu alcance.", cta=True, out="s2_lun_vidaentera")
    _card("fondo_navy_11", P11, "Tu cobertura incluye", "Todo lo esencial, sin complicarte.",
          checklist=["Sin examen médico en planes elegibles", "Tarifa fija de por vida",
                     "Beneficio libre de impuestos", "Se resuelve en una llamada"], out="s2_vie_beneficios")
    _photo("fondo_familia_11", P11, "Atención en español", "Hablemos claro, sin letra chica.",
           "Te explicamos tus opciones sin compromiso.", out="s2_dom_espanol")
    # Week 3
    _card("soc_navy_45_a", P45, "IUL / ahorro", "Un seguro que también acumula ahorro.",
          sub="Protege a tu familia y construye tu retiro, a la vez.", cta=True, out="s3_lun_iul")
    _card("fondo_navy_11b", P11, "Piénsalo", "Tu dinero parado no crece.",
          sub="Con el plan correcto, trabaja para ti y para los tuyos.", cta=True, out="s3_vie_valor")
    _card("soc_navy_11_a", P11, "Tip", "Revisa tu cobertura una vez al año.",
          sub="¿Cuándo fue la última vez que revisaste la tuya?", cta=False, out="s3_dom_tip")
    # Week 4
    _photo("fondo_familia_45", P45, "Dinastía", "Proteger a los tuyos es amor.",
           "El acto de amor más grande empieza hoy.", out="s4_lun_familia")
    _card("soc_navy_11_a", P11, "En 3 pasos", "Proteger a tu familia es simple.",
          checklist=["1 · Llamas y nos cuentas tu caso", "2 · Elegimos el plan a tu medida",
                     "3 · Quedas protegido"], out="s4_vie_pasos")
    _brand("fondo_emblema_11", P11, "Consulta gratis y sin compromiso.", out="s4_dom_consulta")

    # ---------------- CAROUSELS (4:5) ----------------
    nb = ["soc_navy_45_a", "soc_navy_45_b"]
    # c1 mitos
    car_cover(nb[0], "Gastos finales", "3 mitos que te frenan", 5, "c1_mitos_1")
    car_mf(nb[1], 1, 5, "“Soy muy mayor para calificar.”", "Hay planes desde los 50 hasta los 85 años.", "c1_mitos_2")
    car_mf(nb[0], 2, 5, "“Mi salud no me deja.”", "Existen opciones sin examen médico.", "c1_mitos_3")
    car_mf(nb[1], 3, 5, "“Es muy caro.”", "Tarifa fija desde poco al mes, de por vida.", "c1_mitos_4")
    car_cta(nb[0], 4, 5, "Resuélvelo en una sola llamada.", "c1_mitos_5")
    # c2 termino vs vida
    car_cover(nb[1], "Seguro de vida", "¿Término o vida entera?", 5, "c2_vida_1")
    car_body(nb[0], 1, 5, "Término", "Cubre un periodo (10 a 30 años).", "Ideal para deudas o gastos temporales.", "c2_vida_2")
    car_body(nb[1], 2, 5, "Vida entera", "Cubre toda tu vida.", "Tarifa fija + valor en efectivo que se acumula.", "c2_vida_3")
    car_body(nb[0], 3, 5, "Para gastos finales", "La vida entera es la mejor base.", "Protección que no vence y legado para tu familia.", "c2_vida_4")
    car_cta(nb[1], 4, 5, "Te decimos cuál te conviene.", "c2_vida_5")
    # c3 iul
    car_cover(nb[0], "Ahorro + protección", "¿Qué es un IUL?", 5, "c3_iul_1")
    car_body(nb[1], 1, 5, "En simple", "Un seguro de vida que además puede ahorrar.", "Proteges a tu familia y acumulas valor.", "c3_iul_2")
    car_body(nb[0], 2, 5, "Cómo crece", "Ligado a un índice, con un piso protegido.", "Participas de la subida sin exponerte a toda la caída.*", "c3_iul_3")
    car_body(nb[1], 3, 5, "Para quién", "Si buscas protección + ahorro a largo plazo.", "Un plan pensado para tu futuro y el de los tuyos.", "c3_iul_4")
    car_cta(nb[0], 4, 5, "Pregunta cómo funciona, gratis.", "c3_iul_5")
    # c4 por que dinastia
    car_cover(nb[1], "Sobre nosotros", "4 razones para elegir Dinastía", 5, "c4_porque_1")
    car_body(nb[0], 1, 5, "Razón 1", "Atención 100% en español.", "Clara, honesta y sin letra chica.", "c4_porque_2")
    car_body(nb[1], 2, 5, "Razón 2", "Planes a tu medida.", "Gastos finales, vida entera y ahorro.", "c4_porque_3")
    car_body(nb[0], 3, 5, "Razón 3", "Te acompañamos en cada paso.", "Sin presión y sin compromiso.", "c4_porque_4")
    car_cta(nb[1], 4, 5, "Hablemos hoy.", "c4_porque_5")

    print("\nDONE ->", SOC)


def _card(bg, size, *a, **k):
    # thin adapter so single posts share overlay.py's auto-scaling card
    out = k.pop("out")
    _orig_save = ov.save
    ov.save = lambda img, name: save(img, out)
    try:
        ov.piece_card(bg, size, *a, out=out, **k)
    finally:
        ov.save = _orig_save


def _photo(bg, size, eyebrow, headline, sub, out):
    _orig = ov.save
    ov.save = lambda img, name: save(img, out)
    try:
        ov.piece_photo(bg, size, eyebrow, headline, sub, cta=False, out=out)
    finally:
        ov.save = _orig


def _brand(bg, size, tagline, out):
    _orig = ov.save
    ov.save = lambda img, name: save(img, out)
    try:
        ov.piece_brand(bg, size, tagline, out=out)
    finally:
        ov.save = _orig


if __name__ == "__main__":
    main()
