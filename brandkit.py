#!/usr/bin/env python3
"""Load the official Dinastía logo/icons and stamp them onto pieces.

Drop the real assets in brand/ (see brand/COMO_AGREGAR_LOGOS.md). The logo
often ships on a cream/white background; load_logo() removes that background
so it sits cleanly on navy or cream. If no file is present yet, callers fall
back to the text wordmark.
"""

from pathlib import Path

import numpy as np
from PIL import Image

BRAND = Path(__file__).with_name("brand")
_cache = {}


def _remove_bg(im, thresh=222):
    """Make a near-white/cream background transparent (global, for clean-bg logos)."""
    im = im.convert("RGBA")
    a = np.array(im)
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    # near-white/cream + low saturation => background
    mx, mn = np.maximum(np.maximum(r, g), b), np.minimum(np.minimum(r, g), b)
    bg = (mn > thresh) & ((mx - mn) < 22)
    a[..., 3] = np.where(bg, 0, a[..., 3])
    return Image.fromarray(a, "RGBA")


def load_logo(name="logo_principal"):
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        p = BRAND / f"{name}{ext}"
        if p.exists():
            key = str(p)
            if key in _cache:
                return _cache[key]
            im = Image.open(p).convert("RGBA")
            # transparentize only if it looks like it has an opaque light bg
            corners = np.array(im)[[0, -1], :, :3]
            if corners.min() > 200:
                im = _remove_bg(im)
            _cache[key] = im
            return im
    return None


def place_logo(img, size, y_center_frac=0.93, h_frac=0.085, name="logo_principal"):
    """Paste the logo centered horizontally at the given vertical position.
    Returns True if a logo was placed, False if none is available."""
    logo = load_logo(name)
    if logo is None:
        return False
    W, H = size
    th = int(H * h_frac)
    tw = max(1, int(logo.width * th / logo.height))
    r = logo.resize((tw, th), Image.LANCZOS)
    x = (W - tw) // 2
    y = int(H * y_center_frac) - th // 2
    base = img.convert("RGBA")
    base.alpha_composite(r, (x, y))
    img.paste(base.convert("RGB"), (0, 0))
    return True


def has_logo(name="logo_principal"):
    return load_logo(name) is not None
