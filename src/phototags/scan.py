"""Recursive directory scan for image files in sorted order."""

from __future__ import annotations

from pathlib import Path

RAW_EXTENSIONS = frozenset({
    ".cr2", ".cr3", ".nef", ".nrw", ".arw", ".srf", ".sr2",
    ".dng", ".orf", ".rw2", ".pef", ".raw", ".raf", ".3fr",
    ".erf", ".dcr", ".kdc", ".mef", ".mrw", ".x3f", ".cap", ".iiq",
})
IMAGE_EXTENSIONS = frozenset({
    ".jpg", ".jpeg", ".png", ".heic", ".webp",
}) | RAW_EXTENSIONS


def image_paths(root: Path) -> list[Path]:
    """
    Recursively collect image file paths under root, sorted alphabetically by full path.

    Only includes files with extensions in IMAGE_EXTENSIONS. Skips non-files and
    unreadable paths (caller may log and continue).
    """
    root = root.resolve()
    if not root.is_dir():
        return []
    paths: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in IMAGE_EXTENSIONS:
            paths.append(path)
    return sorted(paths)
