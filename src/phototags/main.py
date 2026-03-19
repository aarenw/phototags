"""Main entry point for phototags."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from openai import OpenAI

from phototags.config import Config
from phototags.mllm import analyze_image
from phototags.metadata import has_existing_metadata, write_metadata
from phototags.scan import image_paths
from phototags.thumbnail import make_thumbnail


def _setup_logging(log_dir: Path, verbose: bool) -> None:
    """Configure logging to phototags.log and console."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "phototags.log"
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s %(levelname)s %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"

    root = logging.getLogger("phototags")
    root.setLevel(level)
    root.handlers.clear()

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(logging.Formatter(fmt, datefmt=date_fmt))
    root.addHandler(fh)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(logging.Formatter(fmt, datefmt=date_fmt))
    root.addHandler(ch)


def main() -> None:
    """Run the main application."""
    parser = argparse.ArgumentParser(
        description="Analyze images with an MLLM and write Title, Description, XMP:Subject metadata."
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="Directory to scan recursively for images",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to config file (YAML)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log only; do not write metadata",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip files that already have Title, Description, and XMP:Subject",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()

    config = Config.load(args.config)
    _setup_logging(config.log_dir, args.verbose)
    log = logging.getLogger("phototags")

    directory = args.directory.resolve()
    if not directory.is_dir():
        log.error("Not a directory: %s", directory)
        sys.exit(1)

    client = OpenAI(base_url=config.api_base, api_key=config.api_key or "ollama")

    paths = image_paths(directory)
    log.info("Found %d image(s) under %s", len(paths), directory)

    for path in paths:
        try:
            if args.skip_existing and has_existing_metadata(path):
                log.info("Skip (existing metadata): %s", path)
                continue
        except Exception as e:
            log.debug("Could not read metadata for %s: %s", path, e)

        thumb = make_thumbnail(path, config.thumb_max_dim)
        if thumb is None:
            log.warning("Skipping (unreadable image): %s", path)
            continue

        image_bytes, mime_type = thumb
        result = analyze_image(client, config.model, image_bytes, mime_type)
        if result is None:
            log.error("MLLM analysis failed: %s", path)
            continue

        log.info(
            "Processed %s -> title=%r description=%r keywords=%s",
            path,
            result.title,
            result.description,
            result.keywords,
        )

        if not args.dry_run:
            ok = write_metadata(path, result.title, result.description, result.keywords)
            if not ok:
                log.error("ExifTool write failed: %s", path)


if __name__ == "__main__":
    main()
