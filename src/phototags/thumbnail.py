"""Generate thumbnails for MLLM upload: resize to max dimension, output as bytes."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image

from phototags.scan import RAW_EXTENSIONS


def _load_with_pillow(path: Path) -> Image.Image | None:
    try:
        return Image.open(path).convert("RGB")
    except Exception:
        return None


def _load_raw_with_rawpy(path: Path) -> Image.Image | None:
    try:
        import rawpy
    except ImportError:
        return None
    try:
        with rawpy.imread(str(path)) as raw:
            rgb = raw.postprocess()
        if rgb.dtype != np.uint8:
            rgb = (rgb >> (rgb.dtype.itemsize * 8 - 8)).astype(np.uint8)
        if rgb.ndim == 2:
            rgb = np.stack([rgb] * 3, axis=-1)
        return Image.fromarray(rgb)
    except Exception:
        return None


def make_thumbnail(image_path: Path | str, max_dimension: int) -> tuple[bytes, str] | None:
    """
    Load image, resize so longest side is at most max_dimension, return (jpeg_bytes, mime_type).

    Preserves aspect ratio. Supports RAW formats via rawpy when Pillow cannot open the file.
    Returns None if the image cannot be read.
    """
    path = Path(image_path)
    is_raw = path.suffix.lower() in RAW_EXTENSIONS
    img = _load_with_pillow(path)
    if img is None and is_raw:
        img = _load_raw_with_rawpy(path)
    if img is None:
        return None
    w, h = img.size
    if w <= max_dimension and h <= max_dimension:
        out = img
    else:
        if w >= h:
            new_w = max_dimension
            new_h = int(h * max_dimension / w)
        else:
            new_h = max_dimension
            new_w = int(w * max_dimension / h)
        out = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    buf = BytesIO()
    out.save(buf, format="JPEG", quality=85)
    return (buf.getvalue(), "image/jpeg")
