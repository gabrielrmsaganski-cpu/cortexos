from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DoclingTool:
    def parse(self, path: str) -> dict:
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(path)
        try:
            from docling.document_converter import DocumentConverter  # type: ignore

            converter = DocumentConverter()
            result = converter.convert(path)
            document = result.document
            markdown = document.export_to_markdown()
            return {"path": path, "text": markdown, "available": True}
        except Exception as exc:
            logger.warning("Docling parse failed: %s", exc)
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            return {"path": path, "text": text, "available": False, "error": str(exc)}
