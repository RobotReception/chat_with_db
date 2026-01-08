"""
JSON Sanitizer

Starlette/FastAPI will refuse to serialize NaN/Infinity values (allow_nan=False),
which can lead to 500 errors if pandas/numpy statistics leak into responses.
This module provides a small utility to make payloads JSON-safe.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
import math
from typing import Any
from uuid import UUID


def _is_finite_float(value: float) -> bool:
    try:
        return math.isfinite(value)
    except Exception:
        return False


def sanitize_for_json(obj: Any) -> Any:
    """
    Recursively sanitize an object so it's safe to JSON-encode:
    - Convert NaN/Infinity to None
    - Convert numpy scalars to Python scalars (best-effort)
    - Convert datetime/date/UUID to strings
    - Ensure dict keys are strings
    """
    if obj is None:
        return None

    # primitives
    if isinstance(obj, (str, bool, int)):
        return obj

    # floats (catch NaN/Inf)
    if isinstance(obj, float):
        return obj if _is_finite_float(obj) else None

    # common scalar types
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, Decimal):
        f = float(obj)
        return f if _is_finite_float(f) else None

    # numpy/pandas scalars (optional)
    try:
        import numpy as np  # type: ignore

        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            f = float(obj)
            return f if _is_finite_float(f) else None
        if isinstance(obj, np.bool_):
            return bool(obj)
    except Exception:
        pass

    # containers
    if isinstance(obj, dict):
        return {str(k): sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [sanitize_for_json(v) for v in obj]

    # fallback
    try:
        f = float(obj)  # numpy-like / decimal-like
        return f if _is_finite_float(f) else None
    except Exception:
        return str(obj)

