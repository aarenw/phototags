"""Tests for phototags package."""

import io
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from phototags import __version__
from phototags.config import Config, DEFAULT_API_BASE, DEFAULT_MODEL, DEFAULT_THUMB_MAX_DIM
from phototags.mllm import _parse_analysis_json, _dict_to_result, AnalysisResult
from phototags.scan import image_paths, IMAGE_EXTENSIONS, RAW_EXTENSIONS


def test_version() -> None:
    """Check package version is defined."""
    assert __version__ == "0.1.0"


def test_config_defaults() -> None:
    """Config.load with no file and no env returns defaults."""
    keys = ("PHOTOTAGS_API_BASE", "PHOTOTAGS_MODEL", "PHOTOTAGS_THUMB_MAX_DIM", "PHOTOTAGS_LOG_DIR", "PHOTOTAGS_API_KEY", "OPENAI_API_KEY")
    saved = {k: os.environ.pop(k, None) for k in keys if k in os.environ}
    try:
        cfg = Config.load()
        assert cfg.api_base == DEFAULT_API_BASE
        assert cfg.model == DEFAULT_MODEL
        assert cfg.thumb_max_dim == DEFAULT_THUMB_MAX_DIM
        assert cfg.log_dir.is_absolute()
    finally:
        for k, v in saved.items():
            os.environ[k] = v


def test_config_env_override() -> None:
    """Environment variables override defaults."""
    with patch.dict(
        os.environ,
        {
            "PHOTOTAGS_API_BASE": "http://custom:8080/v1",
            "PHOTOTAGS_MODEL": "custom-model",
            "PHOTOTAGS_THUMB_MAX_DIM": "512",
        },
    ):
        cfg = Config.load()
    assert cfg.api_base == "http://custom:8080/v1"
    assert cfg.model == "custom-model"
    assert cfg.thumb_max_dim == 512


def test_scan_empty_dir(tmp_path: Path) -> None:
    """image_paths on empty dir returns []."""
    assert image_paths(tmp_path) == []


def test_scan_sorted_and_filtered(tmp_path: Path) -> None:
    """image_paths returns only image extensions and in sorted order."""
    (tmp_path / "b.png").write_bytes(b"x")
    (tmp_path / "a.jpg").write_bytes(b"x")
    (tmp_path / "c.txt").write_text("x")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "0.jpeg").write_bytes(b"x")
    paths = image_paths(tmp_path)
    assert len(paths) == 3
    assert paths == sorted(paths)
    exts = {p.suffix.lower() for p in paths}
    assert exts <= IMAGE_EXTENSIONS
    assert ".txt" not in exts


def test_scan_includes_raw(tmp_path: Path) -> None:
    """RAW extensions are included in scan (e.g. .cr2, .dng)."""
    assert ".cr2" in IMAGE_EXTENSIONS and ".cr2" in RAW_EXTENSIONS
    assert ".dng" in IMAGE_EXTENSIONS
    (tmp_path / "photo.cr2").write_bytes(b"dummy")
    paths = image_paths(tmp_path)
    assert len(paths) == 1
    assert paths[0].suffix.lower() == ".cr2"


def test_parse_analysis_json_valid() -> None:
    """_parse_analysis_json returns AnalysisResult for valid JSON."""
    raw = '{"title": "Test", "description": "描述", "keywords": ["a", "b"]}'
    result = _parse_analysis_json(raw)
    assert result is not None
    assert result.title == "Test"
    assert result.description == "描述"
    assert result.keywords == ["a", "b"]


def test_parse_analysis_json_markdown_wrapped() -> None:
    """_parse_analysis_json extracts JSON from markdown code block."""
    text = 'Some text\n```json\n{"title": "T", "description": "D", "keywords": ["k"]}\n```'
    result = _parse_analysis_json(text)
    assert result is not None
    assert result.title == "T"
    assert result.keywords == ["k"]


def test_parse_analysis_json_invalid_returns_none() -> None:
    """_parse_analysis_json returns None for invalid or missing fields."""
    assert _parse_analysis_json("") is None
    assert _parse_analysis_json("not json") is None
    assert _parse_analysis_json('{"title": "T"}') is None  # missing description, keywords


def test_dict_to_result() -> None:
    """_dict_to_result builds AnalysisResult from dict."""
    d = {"title": "T", "description": "D", "keywords": ["x"]}
    r = _dict_to_result(d)
    assert r == AnalysisResult(title="T", description="D", keywords=["x"])
    assert _dict_to_result({"title": "T"}) is None
    r = _dict_to_result({"title": "T", "description": "D", "keywords": []})
    assert r is not None and r.keywords == []


def test_thumbnail_max_dimension(tmp_path: Path) -> None:
    """make_thumbnail resizes so longest side <= max_dimension."""
    from PIL import Image
    from phototags.thumbnail import make_thumbnail

    # Create 200x100 image
    img = Image.new("RGB", (200, 100), color="red")
    path = tmp_path / "test.jpg"
    img.save(path, "JPEG")
    out = make_thumbnail(path, 50)
    assert out is not None
    bytes_out, mime = out
    assert mime == "image/jpeg"
    img_out = Image.open(io.BytesIO(bytes_out))
    assert max(img_out.size) <= 50


def test_metadata_has_existing_no_file() -> None:
    """has_existing_metadata returns False for non-file."""
    from phototags.metadata import has_existing_metadata
    assert has_existing_metadata("/nonexistent/path.jpg") is False


def test_metadata_write_requires_file() -> None:
    """write_metadata returns False for non-file."""
    from phototags.metadata import write_metadata
    assert write_metadata("/nonexistent/path.jpg", "T", "D", ["k"]) is False
