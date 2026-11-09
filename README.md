# aqua3

Python-first port of the AQuA2 (Activity Quantification and Analysis) workflow for molecular spatiotemporal fluorescence signals.

> **Port status:** this repository is an early prototype, not a scientifically
> validated AQuA2 replacement. The language decision, parity requirements, and
> staged migration plan are documented in
> [docs/PORTING_STRATEGY.md](docs/PORTING_STRATEGY.md). The selected approach is
> Python for the application and scientific API, with optional Rust extensions
> only for measured performance bottlenecks.

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

## Activate the project

Requirements: Python 3.10 or newer and a desktop environment capable of
displaying Qt applications.

### One-command environment setup

Clone the complete repository, enter it, and run the setup script for your
operating system. The script creates `.venv`, installs the application and test
dependencies, and verifies the GUI runtime.

Linux or macOS:

```bash
git clone <your-aqua3-repository-url> aqua3
cd aqua3
./scripts/setup-env.sh
source .venv/bin/activate
aqua3
```

Windows PowerShell:

```powershell
git clone <your-aqua3-repository-url> aqua3
cd aqua3
.\scripts\setup-env.ps1
.\.venv\Scripts\Activate.ps1
aqua3
```

By default the scripts use Python 3.11. To select a different Python 3.10+
interpreter, set `AQUA3_PYTHON` before running the script. Set `AQUA3_VENV` to
place the virtual environment somewhere other than `.venv`.

### Conda alternative

If you use Miniconda, Anaconda, or Mambaforge, the checked-in environment file
provides the same application and development dependencies:

```bash
conda env create -f environment.yml
conda activate aqua3
python -m aqua3 --check
aqua3
```

### Linux or macOS

```bash
git clone <your-aqua3-repository-url> aqua3
cd aqua3
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m aqua3 --check
aqua3
```

### Windows PowerShell

```powershell
git clone <your-aqua3-repository-url> aqua3
cd aqua3
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
python -m aqua3 --check
aqua3
```

You can also open a TIFF stack at startup:

```bash
aqua3 path/to/movie.tif
```

The equivalent command that does not rely on the installed launcher is:

```bash
python -m aqua3
```

To stop using the virtual environment, run `deactivate`. To reactivate the
project later, return to the repository and run `source .venv/bin/activate` on
Linux/macOS or `.\.venv\Scripts\Activate.ps1` on Windows, followed by `aqua3`.

### Verify the installation

```bash
python -m aqua3 --version
python -m aqua3 --check
python -m pytest -q
```

`--check` reports any missing GUI dependencies and prints the installation
command needed to repair the environment.

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

## Troubleshooting: local checkout only shows README.md

If your local folder only contains `README.md`, you are probably looking at a checkout that does not include this port commit, or you copied only the initial repository contents. This Python port should include at least these top-level entries:

```text
README.md
pyproject.toml
src/aqua3/
tests/
```

Check your current branch and latest commit:

```bash
git branch --show-current
git log --oneline -5
find . -maxdepth 3 -type f -not -path './.git/*' | sort
```

If `pyproject.toml`, `src/aqua3/app.py`, and `tests/test_model.py` are missing, fetch the branch or pull request that contains the Python port, then check it out. For example:

```bash
git fetch origin
git branch -a
git checkout <branch-with-python-port>
```

If you received a Git bundle instead of a remote branch, clone it with:

```bash
git clone aqua3.bundle aqua3
cd aqua3
```

After the files are present, follow the **Activate the project** instructions
above. The shortest Linux/macOS sequence is:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
aqua3
```
