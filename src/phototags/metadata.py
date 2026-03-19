"""Read and write image metadata via ExifTool (Title, Description, XMP:Subject)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


def has_existing_metadata(image_path: Path | str, exiftool_cmd: str = "exiftool") -> bool:
    """
    Return True if the image has non-empty Title, Description, and XMP:Subject.

    Requires ExifTool to be installed and on PATH (or pass path in exiftool_cmd).
    """
    path = Path(image_path).resolve()
    if not path.is_file():
        return False
    try:
        out = subprocess.run(
            [exiftool_cmd, "-j", "-Title", "-Description", "-Subject", str(path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if out.returncode != 0 or not out.stdout.strip():
            return False
        data = json.loads(out.stdout)
        if not data or not isinstance(data[0], dict):
            return False
        d = data[0]
        title = d.get("Title") or d.get("IPTCObjectName")
        desc = d.get("Description") or d.get("Caption-Abstract") or d.get("IPTC:Caption-Abstract")
        subj = d.get("Subject")
        if isinstance(subj, list):
            subj_ok = len(subj) > 0
        else:
            subj_ok = bool(subj and str(subj).strip())
        return bool(title and str(title).strip()) and bool(desc and str(desc).strip()) and subj_ok
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError, IndexError):
        return False


def write_metadata(
    image_path: Path | str,
    title: str,
    description: str,
    keywords: list[str],
    exiftool_cmd: str = "exiftool",
) -> bool:
    """
    Write Title, Description, and XMP:Subject to the image using ExifTool.

    Returns True on success. Requires ExifTool installed.
    """
    path = Path(image_path).resolve()
    if not path.is_file():
        return False
    args = [exiftool_cmd, "-overwrite_original", f"-Title={title}", f"-Description={description}"]
    for kw in keywords:
        args.append(f"-XMP:Subject={kw}")
    if not keywords:
        args.append("-XMP:Subject=")
    args.append(str(path))
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=60)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
