"""Configuration loading: config file → environment variables → defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

DEFAULT_API_BASE = "http://localhost:11434/v1"
DEFAULT_MODEL = "qwen2.5vl:7b"
DEFAULT_THUMB_MAX_DIM = 600  #1024
CONFIG_FILENAMES = ("phototags.yaml", "phototags.yml")


@dataclass
class Config:
    """Runtime configuration for phototags."""

    api_base: str
    model: str
    api_key: str | None
    thumb_max_dim: int
    log_dir: Path

    @classmethod
    def load(cls, config_path: Path | None = None) -> Config:
        """Load config from file (if path given or found), then env, then defaults."""
        data: dict = {}

        if config_path and config_path.is_file():
            data = _read_config_file(config_path)
        else:
            for candidate in _config_candidates():
                if candidate.is_file():
                    data = _read_config_file(candidate)
                    break

        env_overrides = {
            "api_base": os.environ.get("PHOTOTAGS_API_BASE"),
            "model": os.environ.get("PHOTOTAGS_MODEL"),
            "api_key": os.environ.get("PHOTOTAGS_API_KEY") or os.environ.get("OPENAI_API_KEY"),
            "thumb_max_dim": os.environ.get("PHOTOTAGS_THUMB_MAX_DIM"),
            "log_dir": os.environ.get("PHOTOTAGS_LOG_DIR"),
        }

        api_base = env_overrides["api_base"] or data.get("api_base") or DEFAULT_API_BASE
        model = env_overrides["model"] or data.get("model") or DEFAULT_MODEL
        api_key = env_overrides["api_key"] or data.get("api_key")
        thumb_max_dim_raw = env_overrides["thumb_max_dim"] or data.get("thumb_max_dim", DEFAULT_THUMB_MAX_DIM)
        thumb_max_dim = int(thumb_max_dim_raw) if thumb_max_dim_raw is not None else DEFAULT_THUMB_MAX_DIM
        log_dir_raw = env_overrides["log_dir"] or data.get("log_dir", ".")
        log_dir = Path(log_dir_raw).expanduser().resolve()

        return cls(
            api_base=api_base,
            model=model,
            api_key=api_key,
            thumb_max_dim=thumb_max_dim,
            log_dir=log_dir,
        )


def _config_candidates() -> list[Path]:
    """Return paths to check for config file, in order."""
    cwd = Path.cwd()
    xdg = Path(os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))) / "phototags"
    out: list[Path] = []
    for name in CONFIG_FILENAMES:
        out.append(cwd / name)
    for name in CONFIG_FILENAMES:
        out.append(xdg / name)
    return out


def _read_config_file(path: Path) -> dict:
    """Read YAML config file; return empty dict on error or if yaml not available."""
    if yaml is None:
        return {}
    try:
        text = path.read_text(encoding="utf-8")
        loaded = yaml.safe_load(text)
        return loaded if isinstance(loaded, dict) else {}
    except Exception:
        return {}
