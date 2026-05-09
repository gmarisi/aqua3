# aqua3

Python-first port of the AQuA2 (Activity Quantification and Analysis) workflow for molecular spatiotemporal fluorescence signals.

## What is implemented now

This repository now contains a more faithful AQuA2-oriented Python foundation instead of a generic thresholding demo:

- Python package metadata and an `aqua3` desktop entry point.
- A PySide6 GUI organized around AQuA2-style **Data**, **Detection**, and **Export** tabs.
- A parameter model whose field names mirror AQuA2's `cfg/parameters_for_batch.csv` variable names.
- CSV import for AQuA2 batch-parameter files (`File1`, `File2`, ... columns).
- TIFF stack loading for 2D+time workflows.
- A modular event-detection pipeline following the AQuA2 batch flow:
  1. preprocessing / dF estimation,
  2. active voxel detection,
  3. connected spatiotemporal event labeling,
  4. per-event feature extraction.
- AQuA2-style exports for per-event CSV tables and compressed NumPy arrays.

## Upstream comparison notes

The local `/tmp/AQuA2` directory requested for comparison was not present in this container, and direct clone/download attempts against `https://github.com/yu-lab-vt/AQuA2.git` were blocked by an HTTP 403 tunnel error. I used the public GitHub-rendered source and README text available through the browser tool to align this port with AQuA2's documented batch workflow and parameter names.

AQuA2's documented detection order is: preprocessing/dF, statistical active-region detection, temporal segmentation into super events, and spatial segmentation into events. This Python version implements the same high-level stages with dependency-light NumPy algorithms that are ready to be replaced module-by-module by exact MATLAB parity code.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
aqua3
```

## Python API example

```python
from pathlib import Path

from aqua3.config import load_aqua2_batch_parameters
from aqua3.io import load_tiff_stack, save_detection_outputs
from aqua3.pipeline import AquaPipeline

config = load_aqua2_batch_parameters(Path("cfg/parameters_for_batch.csv"), file_index=1)
movie = load_tiff_stack(Path("example.tif"))
result = AquaPipeline(config).run(movie)
save_detection_outputs(Path("result"), "example", result)
```

## Next steps for full AQuA2 parity

1. Port MATLAB modules stage-by-stage from `pre.*`, `act.*`, `se.*`, `evt.*`, and `fea.*` into the matching Python pipeline functions.
2. Add 3D+time `.mat` import parity and preserve AQuA2's `H, W, L, T` dimensional conventions for volumetric data.
3. Add GUI viewers for overlays, rising maps, propagation maps, side-by-side channels, proofreading/filtering, regions, and landmarks.
4. Add regression tests against known AQuA2 `.mat` outputs and feature tables.
