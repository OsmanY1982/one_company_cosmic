# `iqra/tools/markitdown_tool.py`

> 路径：`iqra/tools/markitdown_tool.py` | 行数：131


---


```python
"""
MarkItDown Tool — Convert any file to Markdown.

Integrates Microsoft's MarkItDown library (https://github.com/microsoft/markitdown)
into the iqra tool registry.  Supports conversion of:

- Documents: PDF, DOCX, PPTX, XLSX
- Images: PNG, JPG, GIF, BMP, TIFF, WebP (via OCR)
- Audio: MP3, WAV, M4A, FLAC (via speech-to-text transcription)
- Web: HTML, CSV, JSON, XML, ZIP archives, YouTube URLs
- Other: EPUB, Outlook MSG, RTF, LaTeX

The tool takes a file path and returns its content as Markdown text.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

from iqra.tools.registry import registry

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

MARKITDOWN_SCHEMA: Dict[str, Any] = {
    "name": "markitdown",
    "description": (
        "Convert a document file to Markdown text. Supports PDF, DOCX, PPTX, "
        "XLSX, images (OCR), audio (transcription), HTML, CSV, JSON, XML, "
        "ZIP archives, EPUB, and more.\n\n"
        "Provide an absolute file path and receive the file's text content "
        "as clean Markdown. This is the universal file reader — use it "
        "when you need to extract readable text from any supported format."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": (
                    "Absolute path to the file to convert. Must be a supported "
                    "format: .pdf / .docx / .pptx / .xlsx / .png / .jpg / "
                    ".mp3 / .wav / .html / .csv / .json / .epub / .zip etc."
                ),
            },
        },
        "required": ["file_path"],
    },
    "output": {"type": "string", "description": "Markdown text extracted from the file"},
}


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------

def markitdown_convert(file_path: str) -> str:
    """Convert a file to Markdown using MarkItDown.

    Args:
        file_path: Absolute path to the source file.

    Returns:
        JSON-encoded result with ``success``, ``content`` (Markdown string),
        and optional ``error`` fields.
    """
    import os

    if not os.path.isfile(file_path):
        return json.dumps({
            "success": False,
            "error": f"File not found: {file_path}",
        })

    try:
        from markitdown import MarkItDown
    except ImportError:
        return json.dumps({
            "success": False,
            "error": (
                "MarkItDown library is not installed. "
                "Run: pip install markitdown"
            ),
        })

    try:
        md = MarkItDown()
        result = md.convert(file_path)
        return json.dumps({
            "success": True,
            "content": result.text_content,
        }, ensure_ascii=False)
    except Exception as exc:
        logger.exception("MarkItDown conversion failed for %s", file_path)
        return json.dumps({
            "success": False,
            "error": f"Conversion failed: {exc}",
        })


# ---------------------------------------------------------------------------
# Check function — only register if markitdown is importable
# ---------------------------------------------------------------------------

def _markitdown_check() -> bool:
    """Tool availability gate: markitdown package must be installed."""
    try:
        import markitdown  # noqa: F401
        return True
    except ImportError:
        return False


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

registry.register(
    name="markitdown",
    toolset="document-processing",
    schema=MARKITDOWN_SCHEMA,
    handler=lambda args, **kw: markitdown_convert(args["file_path"]),
    check_fn=_markitdown_check,
    description="Convert documents (PDF/DOCX/PPTX/XLSX/images/audio/HTML) to Markdown text",
    emoji="📄",
)

```
