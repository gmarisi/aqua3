from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np

from .model import AnalysisConfig


@dataclass(slots=True)
class EventFeature:
    event_id: int
    channel: int
    start_frame: int
    end_frame: int
    duration_frames: int
    duration_seconds: float
    area_pixels: int
    area_physical: float
    voxel_count: int
    peak_frame: int
    peak_dff: float
    mean_dff: float
    auc: float
    centroid_y: float
    centroid_x: float

    def to_row(self) -> dict[str, int | float]:
        return {
            "event_id": self.event_id,
            "channel": self.channel,
            "start_frame": self.start_frame,
            "end_frame": self.end_frame,
            "duration_frames": self.duration_frames,
            "duration_seconds": self.duration_seconds,
            "area_pixels": self.area_pixels,
            "area_physical": self.area_physical,
            "voxel_count": self.voxel_count,
            "peak_frame": self.peak_frame,
            "peak_dff": self.peak_dff,
            "mean_dff": self.mean_dff,
            "auc": self.auc,
            "centroid_y": self.centroid_y,
            "centroid_x": self.centroid_x,
        }


@dataclass(slots=True)
class PipelineResult:
    baseline: np.ndarray
    dff: np.ndarray
    noise: np.ndarray
    active_mask: np.ndarray
    event_labels: np.ndarray
    events: list[EventFeature]

    @property
    def denoised(self) -> np.ndarray:
        return self.dff

    @property
    def score_map(self) -> np.ndarray:
        return np.max(self.dff, axis=0)

    @property
    def events_mask(self) -> np.ndarray:
        return self.event_labels > 0


class AquaPipeline:
    """AQuA2-inspired event-detection pipeline in Python.

    The implementation follows the public AQuA2 batch workflow order:
    preprocessing/dF, active-region detection, temporal/spatial event labeling,
    then feature-table extraction. It is intentionally modular so each MATLAB
    stage can be replaced by a parity implementation as the port progresses.
    """

    def __init__(self, config: AnalysisConfig) -> None:
        self.config = config

    def run(self, stack: np.ndarray) -> PipelineResult:
        movie = canonicalize_movie(stack)
        baseline = estimate_baseline(movie, self.config.movAvgWin)
        dff = compute_dff(movie, baseline)
        dff = median_filter_3x3(dff, self.config.medSmo)
        noise = estimate_noise(dff, self.config.varEst)
        active_mask = detect_active_voxels(dff, noise, self.config.thrARScl)
        event_labels = label_events(active_mask, self.config)
        events = extract_event_features(event_labels, dff, self.config)
        return PipelineResult(
            baseline=baseline,
            dff=dff,
            noise=noise,
            active_mask=active_mask,
            event_labels=event_labels,
            events=events,
        )


def canonicalize_movie(stack: np.ndarray) -> np.ndarray:
    """Return data as ``(time, y, x)`` for the first Python port milestone."""
    array = np.asarray(stack, dtype=np.float32)
    if array.ndim == 2:
        return array[np.newaxis, :, :]
    if array.ndim == 3:
        return array
    if array.ndim == 4:
        if array.shape[-1] <= min(array.shape[:3]):
            array = np.moveaxis(array, -1, 0)
        return array.reshape(array.shape[0], -1, array.shape[-1])
    msg = f"Unsupported movie dimensionality: {array.shape!r}"
    raise ValueError(msg)


def estimate_baseline(movie: np.ndarray, window: int) -> np.ndarray:
    """Estimate a slowly varying fluorescence baseline with rolling percentiles."""
    window = max(1, int(window))
    if movie.shape[0] == 1 or window == 1:
        return np.maximum(movie.copy(), 1e-6)

    baseline = np.empty_like(movie, dtype=np.float32)
    radius = window // 2
    for frame in range(movie.shape[0]):
        start = max(0, frame - radius)
        end = min(movie.shape[0], frame + radius + 1)
        baseline[frame] = np.percentile(movie[start:end], 20, axis=0)
    return np.maximum(baseline, 1e-6)


def compute_dff(movie: np.ndarray, baseline: np.ndarray) -> np.ndarray:
    return (movie - baseline) / baseline


def median_filter_3x3(movie: np.ndarray, radius: int) -> np.ndarray:
    """Small dependency-free spatial median filter for salt-and-pepper noise."""
    radius = int(radius)
    if radius <= 0:
        return movie
    padded = np.pad(movie, ((0, 0), (radius, radius), (radius, radius)), mode="edge")
    filtered = np.empty_like(movie)
    size = 2 * radius + 1
    for y in range(movie.shape[1]):
        for x in range(movie.shape[2]):
            patch = padded[:, y : y + size, x : x + size]
            filtered[:, y, x] = np.median(patch, axis=(1, 2))
    return filtered


def estimate_noise(dff: np.ndarray, var_estimate: float) -> np.ndarray:
    """Estimate per-pixel noise using frame-to-frame differences."""
    if dff.shape[0] < 2:
        return np.full(dff.shape[1:], max(float(var_estimate), 1e-6), dtype=np.float32)
    diff = np.diff(dff, axis=0)
    sigma = np.median(np.abs(diff - np.median(diff, axis=0)), axis=0) / 0.6745
    sigma = sigma / np.sqrt(2.0)
    fallback = np.sqrt(max(float(var_estimate), 1e-12))
    sigma = np.where(sigma > 0, sigma, fallback)
    return sigma.astype(np.float32, copy=False)


def detect_active_voxels(dff: np.ndarray, noise: np.ndarray, threshold_scale: float) -> np.ndarray:
    threshold = np.asarray(noise) * float(threshold_scale)
    return dff > threshold[np.newaxis, :, :]


def label_events(active_mask: np.ndarray, config: AnalysisConfig) -> np.ndarray:
    labels = np.zeros(active_mask.shape, dtype=np.int32)
    current = 0
    min_size = max(1, int(config.minSize))
    max_size = int(config.maxSize) if np.isfinite(config.maxSize) else None
    min_duration = max(1, int(config.minDur))

    for index in zip(*np.nonzero(active_mask)):
        if labels[index] != 0:
            continue
        voxels = flood_fill(active_mask, labels, index, current + 1)
        if not voxels:
            continue
        frames = [voxel[0] for voxel in voxels]
        duration = max(frames) - min(frames) + 1
        spatial_area = len({(voxel[1], voxel[2]) for voxel in voxels})
        too_small = spatial_area < min_size or duration < min_duration
        too_large = max_size is not None and spatial_area > max_size
        if too_small or too_large:
            for voxel in voxels:
                labels[voxel] = 0
            continue
        current += 1

    return relabel_consecutively(labels)


def flood_fill(
    active_mask: np.ndarray,
    labels: np.ndarray,
    start: tuple[int, int, int],
    label: int,
) -> list[tuple[int, int, int]]:
    queue: deque[tuple[int, int, int]] = deque([start])
    labels[start] = label
    voxels: list[tuple[int, int, int]] = []
    shape = active_mask.shape
    while queue:
        t, y, x = queue.popleft()
        voxels.append((t, y, x))
        for nt, ny, nx in neighbors(t, y, x, shape):
            if active_mask[nt, ny, nx] and labels[nt, ny, nx] == 0:
                labels[nt, ny, nx] = label
                queue.append((nt, ny, nx))
    return voxels


def neighbors(t: int, y: int, x: int, shape: tuple[int, int, int]):
    max_t, max_y, max_x = shape
    for dt, dy, dx in (
        (-1, 0, 0),
        (1, 0, 0),
        (0, -1, 0),
        (0, 1, 0),
        (0, 0, -1),
        (0, 0, 1),
    ):
        nt = t + dt
        ny = y + dy
        nx = x + dx
        if 0 <= nt < max_t and 0 <= ny < max_y and 0 <= nx < max_x:
            yield nt, ny, nx


def relabel_consecutively(labels: np.ndarray) -> np.ndarray:
    result = np.zeros_like(labels)
    for new_label, old_label in enumerate(np.unique(labels[labels > 0]), start=1):
        result[labels == old_label] = new_label
    return result


def extract_event_features(
    labels: np.ndarray,
    dff: np.ndarray,
    config: AnalysisConfig,
) -> list[EventFeature]:
    events: list[EventFeature] = []
    for event_id in np.unique(labels[labels > 0]):
        positions = np.argwhere(labels == event_id)
        values = dff[labels == event_id]
        frames = positions[:, 0]
        ys = positions[:, 1]
        xs = positions[:, 2]
        peak_idx = int(np.argmax(values))
        area_pixels = len(set(zip(ys.tolist(), xs.tolist())))
        duration_frames = int(frames.max() - frames.min() + 1)
        events.append(
            EventFeature(
                event_id=int(event_id),
                channel=1,
                start_frame=int(frames.min()),
                end_frame=int(frames.max()),
                duration_frames=duration_frames,
                duration_seconds=duration_frames / float(config.frameRate),
                area_pixels=area_pixels,
                area_physical=area_pixels * float(config.spatialRes) ** 2,
                voxel_count=int(positions.shape[0]),
                peak_frame=int(frames[peak_idx]),
                peak_dff=float(values[peak_idx]),
                mean_dff=float(values.mean()),
                auc=float(values.sum() / float(config.frameRate)),
                centroid_y=float(ys.mean()),
                centroid_x=float(xs.mean()),
            )
        )
    return events
