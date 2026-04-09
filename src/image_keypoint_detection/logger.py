from __future__ import annotations

import json
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any


def setup_logger(log_path: str) -> logging.Logger:
    resolved_log_path = resolve_log_file_path(log_path)
    logger = logging.getLogger("image_keypoint_detection")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if _has_handler(logger, str(resolved_log_path)):
        return logger

    resolved_log_path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(resolved_log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    return logger


def log_event(logger: logging.Logger, **fields: Any) -> None:
    logger.info(json.dumps(fields, ensure_ascii=False))


def build_error_fields(exc: Exception) -> dict[str, str]:
    return {
        "error_message": str(exc),
        "stack_trace": "".join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        ).strip(),
    }


def resolve_log_file_path(log_path: str) -> Path:
    path = Path(log_path)
    if path.suffix:
        log_dir = path.parent
    else:
        log_dir = path

    return log_dir / f"{datetime.now().date().isoformat()}.log"


def _has_handler(logger: logging.Logger, log_path: str) -> bool:
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            if Path(handler.baseFilename) == Path(log_path):
                return True
    return False
