from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

import numpy as np
import tifffile

from .pipeline import EventFeature, PipelineResult


def load_tiff_stack(path: Path) -> np.ndarray:
    """Load a 2D/3D/4D TIFF stack as float32.

    AQuA2 uses TIFF/TIFF stacks for 2D+time data and treats 3D+time as a
    separate path. This loader keeps dimensionality intact and normalizes only
    dtype, leaving axis interpretation to the pipeline.
    """
    stack = tifffile.imread(path)
    if stack.ndim < 2:
        msg = f"Expected image stack with >=2 dims, got shape {stack.shape!r}"
        raise ValueError(msg)
    return stack.astype(np.float32, copy=False)


def save_event_table(path: Path, events: Iterable[EventFeature]) -> None:
    """Write an AQuA2-inspired per-event feature table."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "event_id",
        "channel",
        "start_frame",
        "end_frame",
        "duration_frames",
        "duration_seconds",
        "area_pixels",
        "area_physical",
        "voxel_count",
        "peak_frame",
        "peak_dff",
        "mean_dff",
        "auc",
        "centroid_y",
        "centroid_x",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for event in events:
            writer.writerow(event.to_row())


def save_detection_outputs(output_dir: Path, name: str, result: PipelineResult) -> None:
    """Persist Python-port outputs using names similar to AQuA2 batch exports."""
    output_dir.mkdir(parents=True, exist_ok=True)
    save_event_table(output_dir / f"{name}_AQuA3_Ch1.csv", result.events)
    np.savez_compressed(
        output_dir / f"{name}_AQuA3_arrays.npz",
        dff=result.dff,
        active_mask=result.active_mask,
        event_labels=result.event_labels,
        baseline=result.baseline,
        noise=result.noise,
    )
