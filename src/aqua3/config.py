from __future__ import annotations

import csv
import math
from dataclasses import fields
from pathlib import Path
from typing import Any

from .model import AnalysisConfig

_BOOLEAN_FIELDS = {
    field.name
    for field in fields(AnalysisConfig)
    if field.type is bool or field.type == "bool"
}


def coerce_parameter_value(raw: str) -> bool | int | float | str:
    value = raw.strip()
    if value == "":
        return value
    if value.lower() == "inf":
        return math.inf
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    try:
        numeric = float(value)
    except ValueError:
        return value
    if numeric.is_integer():
        return int(numeric)
    return numeric


def load_aqua2_batch_parameters(path: Path, file_index: int = 1) -> AnalysisConfig:
    """Load one FileN column from AQuA2's batch-parameter CSV.

    AQuA2's MATLAB batch script calls ``util.parseParam_for_batch(xxx)`` for
    each input file. This function provides the equivalent Python behavior for
    the public ``cfg/parameters_for_batch.csv`` layout.
    """
    if file_index < 1:
        msg = "file_index is 1-based and must be >= 1"
        raise ValueError(msg)

    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        column = f"File{file_index}"
        if reader.fieldnames is None or column not in reader.fieldnames:
            msg = f"Parameter file does not contain {column!r}"
            raise ValueError(msg)

        values: dict[str, Any] = {}
        valid_names = {field.name for field in fields(AnalysisConfig)}
        for row in reader:
            variable = (row.get("Variable") or "").strip()
            if variable not in valid_names:
                continue
            value = coerce_parameter_value(row.get(column, ""))
            if variable in _BOOLEAN_FIELDS:
                value = bool(value)
            values[variable] = value

    return AnalysisConfig(**values)
