"""MLLM integration: OpenAI-compatible API, image analysis, structured JSON output."""

from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass

from openai import OpenAI


ANALYSIS_PROMPT = """Analyze this image and respond with a JSON object only (no other text). Use this exact structure:
{"title": "a short title in English or Chinese", "description": "a detailed description in Chinese, under 50 characters", "keywords": ["keyword1", "keyword2", ...]}

Rules: description must be under 50 Chinese characters. keywords should be subject tags suitable for search (in Chinese or English). Return only the JSON object."""


@dataclass
class AnalysisResult:
    """Structured result from the MLLM."""

    title: str
    description: str
    keywords: list[str]


def analyze_image(
    client: OpenAI,
    model: str,
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
) -> AnalysisResult | None:
    """
    Send image to the model and parse structured JSON (title, description, keywords).

    Returns None on API or parse failure.
    """
    b64 = base64.standard_b64encode(image_bytes).decode("ascii")
    data_uri = f"data:{mime_type};base64,{b64}"

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": ANALYSIS_PROMPT},
                        {"type": "image_url", "image_url": {"url": data_uri}},
                    ],
                }
            ],
            max_tokens=512,
        )
    except Exception:
        return None

    text = (response.choices[0].message.content or "").strip()
    parsed = _parse_analysis_json(text)
    return parsed


def _parse_analysis_json(text: str) -> AnalysisResult | None:
    """Extract JSON from model output, optionally inside markdown code blocks."""
    if not text:
        return None
    # Try raw parse first
    obj = _try_parse_json(text)
    if obj is not None:
        return _dict_to_result(obj)
    # Strip markdown code block
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        obj = _try_parse_json(match.group(1).strip())
        if obj is not None:
            return _dict_to_result(obj)
    # Try to find first {...}
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        obj = _try_parse_json(match.group(0))
        if obj is not None:
            return _dict_to_result(obj)
    return None


def _try_parse_json(s: str) -> dict | None:
    try:
        out = json.loads(s)
        return out if isinstance(out, dict) else None
    except (json.JSONDecodeError, TypeError):
        return None


def _dict_to_result(d: dict) -> AnalysisResult | None:
    try:
        title = d.get("title")
        description = d.get("description")
        keywords = d.get("keywords")
        if title is None or description is None or keywords is None:
            return None
        if not isinstance(keywords, list):
            keywords = [str(k) for k in keywords] if keywords else []
        else:
            keywords = [str(k) for k in keywords]
        return AnalysisResult(
            title=str(title).strip(),
            description=str(description).strip(),
            keywords=keywords,
        )
    except (TypeError, ValueError):
        return None
