# **Project Overview**
The objective of this project is to leverage Multimodal Large Language Models (MLLMs) to analyze image content and automatically populate metadata fields—specifically `Title`, `Description`, and `XMP:Subject`. This automation facilitates seamless text-based searching within photo management systems.

**Key Requirements:**
* **Automated Content Analysis:** The system recursively scans a specified directory (including subdirectories) and utilizes an MLLM to return analysis results in a structured JSON/dictionary format containing a concise title, a detailed description (under 50 Chinese characters), and an array of subject keywords.
* **Metadata Integration:** Upon receiving the model's output, the tool utilizes [ExifTool](https://exiftool.org/) to write the `Title`, `Description`, and `XMP:Subject` directly into the file's metadata.
* **Logging and Observability:** Every processed file is logged to both `phototags.log` and the console. Each entry includes a timestamp, the full file path, and the model's returned data.
* **Performance Optimization:** To minimize token consumption and reduce latency, the system generates and uploads thumbnails rather than full-resolution images. The maximum dimension of these thumbnails is user-configurable.
* **Flexible Configuration:** System parameters—including log directories, thumbnail constraints, API endpoints, model names, and authentication tokens—are managed via a hierarchy: Configuration File (Primary) > Environment Variables (Secondary) > Default Values (Fallback).
* **API Compatibility:** The model server must adhere to the OpenAI API standard, with **Ollama** as the default provider and **qwen2.5-vl:7b** as the default model.

## Prerequisites

- **Python 3.11+**
- **ExifTool** — must be installed and on your `PATH`. See [exiftool.org](https://exiftool.org/) for installation.
- An OpenAI-compatible API (e.g. **Ollama** with a vision model such as `qwen2.5-vl:7b`).

**Supported image formats:** JPEG, PNG, HEIC, WebP; plus RAW (CR2, CR3, NEF, NRW, ARW, DNG, ORF, RW2, PEF, RAF, 3FR, and other LibRaw-supported RAW formats). RAW thumbnails are generated via the `rawpy` library.

## Installation

```bash
# With uv (recommended)
uv sync
# Or with pip
pip install -e ".[dev]"
```

## Usage

```bash
# Process all images under a directory (default: Ollama at localhost:11434)
phototags /path/to/photos

# Skip files that already have Title, Description, and XMP:Subject
phototags /path/to/photos --skip-existing

# Dry run: analyze and log only, do not write metadata
phototags /path/to/photos --dry-run

# Custom config file and verbose logging
phototags /path/to/photos --config ./phototags.yaml --verbose
```

## Configuration

**Priority:** Config file → Environment variables → Defaults.

**Config file:** Place `phototags.yaml` (or `phototags.yml`) in the current directory or in `~/.config/phototags/`. Use `--config /path/to/file.yaml` to specify a path.

Example `phototags.yaml`:

```yaml
api_base: "http://localhost:11434/v1"
model: "qwen2.5-vl:7b"
api_key: null
thumb_max_dim: 1024
log_dir: "."
```

**Environment variables:**

| Variable | Description |
|----------|-------------|
| `PHOTOTAGS_API_BASE` | API base URL (default: `http://localhost:11434/v1`) |
| `PHOTOTAGS_MODEL` | Model name (default: `qwen2.5-vl:7b`) |
| `PHOTOTAGS_API_KEY` or `OPENAI_API_KEY` | API key (optional for Ollama) |
| `PHOTOTAGS_THUMB_MAX_DIM` | Max thumbnail dimension in pixels (default: 1024) |
| `PHOTOTAGS_LOG_DIR` | Directory for `phototags.log` (default: current directory) |

## 项目结构

```
phototags/
├── src/
│   └── phototags/
│       ├── __init__.py
│       ├── config.py
│       ├── main.py
│       ├── mllm.py
│       ├── metadata.py
│       ├── scan.py
│       └── thumbnail.py
├── tests/
│   ├── __init__.py
│   └── test_phototags.py
├── main.py
├── pyproject.toml
└── README.md
```

## 开发

```bash
# 安装（可编辑模式 + 开发依赖）
uv sync
# 或 pip install -e ".[dev]"

# 运行
uv run python main.py /path/to/photos
# 或安装后：phototags /path/to/photos

# 测试
uv run pytest
# 或 pytest
```
