from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class AnalysisConfig:
    """AQuA2-compatible analysis settings.

    Field names intentionally mirror the variable names in AQuA2's
    ``cfg/parameters_for_batch.csv`` so MATLAB batch settings can be translated
    directly into the Python port.
    """

    registrateCorrect: int = 1
    bleachCorrect: int = 1
    medSmo: int = 0
    smoXY: float = 0.5
    thrARScl: float = 3.0
    minDur: int = 5
    minSize: int = 20
    maxSize: float = float("inf")
    circularityThr: float = 0.0
    spaMergeDist: int = 0
    needTemp: bool = True
    seedSzRatio: float = 0.01
    sigThr: float = 3.5
    maxDelay: float = 0.6
    needRefine: bool = False
    needGrow: bool = False
    needSpa: bool = True
    sourceSzRatio: float = 0.01
    sourceSensitivity: int = 8
    whetherExtend: bool = True
    detectGlo: bool = False
    gloDur: int = 20
    ignoreTau: bool = True
    propMetric: bool = False
    networkFeatures: bool = False
    gtwSmo: float = 0.2
    ratio: float = 0.5
    regMaskGap: int = 5
    cut: int = 200
    movAvgWin: int = 25
    minShow1: float = 0.2
    correctTrend: bool = True
    propthrmin: float = 0.5
    propthrstep: float = 0.1
    propthrmax: float = 0.5
    compress: float = 0.0
    gapExt: int = 5
    TPatch: int = 20
    maxSpaScale: int = 7
    minSpaScale: int = 3
    frameRate: float = 0.5
    spatialRes: float = 0.5
    varEst: float = 0.02
    fgFluo: float = 0.0
    bgFluo: float = 0.0
    northx: float = 0.0
    northy: float = 1.0

    @property
    def temporal_smoothing(self) -> int:
        """Backward-compatible alias used by the first scaffold GUI."""
        return self.movAvgWin

    @temporal_smoothing.setter
    def temporal_smoothing(self, value: float) -> None:
        self.movAvgWin = max(1, int(round(value)))

    @property
    def z_threshold(self) -> float:
        """Backward-compatible alias for active-region threshold scale."""
        return self.thrARScl

    @z_threshold.setter
    def z_threshold(self, value: float) -> None:
        self.thrARScl = float(value)

    @property
    def min_event_pixels(self) -> int:
        """Backward-compatible alias for AQuA2's minimum active-region size."""
        return self.minSize

    @min_event_pixels.setter
    def min_event_pixels(self, value: int) -> None:
        self.minSize = int(value)


@dataclass(slots=True)
class ProjectState:
    data_path: Path | None = None
    output_dir: Path | None = None
    shape: tuple[int, ...] | None = None
    config: AnalysisConfig = field(default_factory=AnalysisConfig)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["data_path"] = str(self.data_path) if self.data_path else None
        payload["output_dir"] = str(self.output_dir) if self.output_dir else None
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ProjectState":
        config_payload = payload.get("config", {})
        config = AnalysisConfig(**config_payload)
        data_path = payload.get("data_path")
        output_dir = payload.get("output_dir")
        shape = payload.get("shape")
        return cls(
            data_path=Path(data_path) if data_path else None,
            output_dir=Path(output_dir) if output_dir else None,
            shape=tuple(shape) if shape else None,
            config=config,
        )
