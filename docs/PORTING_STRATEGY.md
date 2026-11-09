# AQuA2 language evaluation and porting strategy

Status: **decision proposed; parity work not yet started**  
Upstream: <https://github.com/yu-lab-vt/AQuA2>  
Upstream license: GPL-2.0

## Executive decision

Use **Python as the product language** and reserve **Rust for measured compute
hotspots** exposed to Python through PyO3/maturin.

Do not rewrite the whole application in Rust first. AQuA2 is a scientific
application whose behavior depends on MATLAB array semantics, statistical and
image-processing routines, MAT/TIFF interoperability, plots, and interactive
workflows. Python has direct, mature equivalents for those concerns and is the
lower-risk path to numerical parity. Rust is valuable later for bounded kernels
where profiling proves that NumPy, SciPy, Numba, or scikit-image are
insufficient.

The existing `aqua3.pipeline` is a prototype, **not an AQuA2-compatible port**.
It must not be used for scientific conclusions until the parity gates in this
document pass.

## Evidence from upstream

The upstream repository is larger than its four headline detection stages. Its
`src` tree is split into MATLAB packages for active regions, bursts, CFUs,
events, features, global events, images, I/O, multi-session alignment,
plotting, preprocessing, registration, super-events, UI, and utilities. It also
contains BILCO/MEX code, configuration MAT files, two GUIs, event batch entry
points, CFU batch/viewer entry points, 2D and 3D support, and dual-channel
workflows.

The documented event pipeline is:

1. preprocessing and dF estimation;
2. statistical active-region detection;
3. temporal segmentation into super-events;
4. spatial segmentation into events;
5. feature extraction, visualization, proofreading, and export;
6. optional global-event and CFU analysis.

The MATLAB implementation depends on Image Processing, Statistics and Machine
Learning, Signal Processing, and Curve Fitting toolboxes. This dependency shape
strongly favors a Python scientific stack for the first complete port.

## Python versus Rust

Scores are 1 (poor) to 5 (strong), weighted for this project rather than for
general-purpose software.

| Criterion | Weight | Python | Rust | Why it matters here |
|---|---:|---:|---:|---|
| MATLAB/NumPy translation fidelity | 20 | 5 | 2 | Array slicing, broadcasting, NaN behavior, and column-major assumptions dominate the algorithms. |
| Scientific/image ecosystem | 20 | 5 | 3 | NumPy, SciPy, scikit-image, pandas, tifffile, h5py, and napari cover most toolbox roles. |
| GUI and scientific visualization | 10 | 4 | 2 | PySide6, pyqtgraph, matplotlib, and napari are mature and composable. |
| Performance ceiling | 15 | 3 | 5 | Rust wins for custom graph, dynamic-programming, and segmentation kernels. |
| Memory safety and concurrency | 10 | 3 | 5 | Rust is stronger, especially for long-running batch jobs. |
| Iteration speed for scientists | 15 | 5 | 2 | Python is easier to inspect, compare with MATLAB, and modify interactively. |
| Packaging and deployment | 5 | 3 | 4 | Rust binaries are simpler; Python desktop packaging is manageable but needs CI. |
| Contributor accessibility | 5 | 5 | 2 | The target scientific community is much more likely to know Python. |
| **Weighted total / 500** | **100** | **430** | **315** | **Python wins for the primary implementation.** |

### Recommended technology map

| Concern | Initial implementation | Escalation path |
|---|---|---|
| N-dimensional arrays | NumPy | Rust `ndarray` only behind a stable Python API |
| Filtering/statistics/optimization | SciPy | Numba, then Rust if profiling warrants it |
| Morphology/segmentation | scikit-image + SciPy | Rust kernel for identified bottlenecks |
| Tables/features | pandas or Polars | Arrow/Polars native path for very large tables |
| TIFF/OME-TIFF | tifffile + imagecodecs | Rust `tiff` only if required formats are unsupported |
| MAT v5/v7.3 | scipy.io + h5py | Dedicated compatibility layer |
| Desktop GUI | PySide6 + pyqtgraph/napari components | Keep algorithms independent from Qt |
| Packaging | pyproject + cibuildwheel/PyInstaller | maturin for optional Rust wheels |

## Non-negotiable rules

1. **Freeze an upstream revision.** Record the AQuA2 commit hash and GPL-2.0
   license before translating code. Never port against a moving `main` branch.
2. **Black-box before rewrite.** Capture MATLAB inputs, options, intermediate
   arrays, outputs, and feature tables before implementing each stage.
3. **Preserve semantics explicitly.** Document axis order, 1-based versus
   0-based indexes, MATLAB linear indexes, connectivity, boundary conditions,
   floating-point dtype, NaN handling, random seeds, and tie-breaking.
4. **Separate core and UI.** The batch API must have no Qt dependency. The GUI
   invokes the same public pipeline used by CLI tests.
5. **No parity claim without fixtures.** A function is not “ported” because it
   runs; it is ported only when its agreed reference fixtures pass.
6. **Optimize last.** First obtain correctness in vectorized Python. Profile
   realistic data, then use Numba or Rust only for demonstrated bottlenecks.
7. **Respect GPL-2.0.** A derivative translation must retain compatible
   licensing and source-distribution obligations. Obtain legal review before
   distributing binaries or combining code under a different license.

## Multi-step port sequence

### Phase 0 — Governance and source freeze

Deliverables:

- upstream repository vendored as a Git submodule or fetched in CI at a pinned
  commit;
- recorded license and citation metadata;
- module inventory generated with `tools/inventory_matlab.py`;
- issue tracker with one parity ticket per MATLAB function/package;
- representative datasets whose redistribution terms are known.

Exit gate: every source file belongs to an owner, phase, and test category.

### Phase 1 — MATLAB reference harness

Build a MATLAB script that runs individual stages and writes versioned fixtures
containing inputs, options, intermediate arrays, and outputs. Include tiny
synthetic cases where expected behavior can be inspected manually and real
cropped datasets for statistical realism.

Fixture requirements:

- MAT v7.3 or HDF5 with explicit axis metadata;
- MATLAB release, OS, toolbox versions, AQuA2 commit, and RNG state;
- exact integer/boolean labels and toleranced floating-point arrays;
- 2D+t, 3D+t, single-channel, dual-channel, empty, border, NaN, and constant
  input cases.

Exit gate: the frozen MATLAB version reproduces every fixture deterministically.

### Phase 2 — Python contracts and I/O

Define stable typed contracts before translating algorithms:

- `Movie`: canonical `(T, Z, Y, X, C)` axis order plus calibration metadata;
- validated options grouped by pipeline stage;
- event/super-event sparse label representation;
- feature schema with units and missing-value rules;
- import/export compatibility for TIFF, AVI, MAT v5/v7.3, masks, parameter CSV,
  and AQuA2 result files.

Exit gate: Python can round-trip reference inputs and outputs without running
detection, including MATLAB index conversions.

### Phase 3 — Preprocessing parity (`+pre`, registration, image utilities)

Port baseline/noise estimation, bleaching correction, smoothing, registration,
and dF generation. Keep each MATLAB function mapped to a focused Python
function, even if later refactoring combines them.

Exit gate: intermediate arrays pass fixture tolerances across all dimensions and
edge cases.

### Phase 4 — Active regions (`+act`)

Port statistical testing, thresholding, connectivity, and active-region
filtering. Match MATLAB connected-component connectivity and label ordering
exactly before considering a faster implementation.

Exit gate: active masks are exact; region statistics meet defined tolerances.

### Phase 5 — Temporal segmentation / super-events (`+se`, BILCO)

This is the highest-risk algorithm phase. Translate seed detection, order
statistics, growing/merging, curve significance, watershed logic, and the
BILCO/MEX functionality. Start with a readable Python reference implementation.
Profile it only after parity; BILCO is a likely Rust candidate.

Exit gate: seed sets, merge graphs, super-event labels, and temporal order maps
match fixtures.

### Phase 6 — Spatial segmentation and events (`+evt`, `+burst`, `+glo`)

Port event splitting, propagation-aware segmentation, global-event handling,
and optional refinement/growth. Preserve deterministic label identity through a
documented relabeling policy.

Exit gate: event voxel sets match exactly or satisfy an explicitly approved IoU
and temporal-overlap contract; event counts and ordering are deterministic.

### Phase 7 — Features (`+fea`)

Port basic, curve, propagation, landmark, region, and network features. Define
units and names centrally rather than duplicating GUI labels.

Exit gate: integer/categorical fields are exact and floating-point fields meet
per-feature tolerances on the complete reference corpus.

### Phase 8 — CFU and multi-session analysis (`+cfu`, `+multiAlign`)

Port CFU identification, dependency/delay analysis, grouping, manual division,
multi-session field-of-view registration, and batch result compatibility.

Exit gate: CFU maps, event membership, dependency matrices, delays, and groups
match the current upstream result schema.

### Phase 9 — Batch CLI

Reproduce `aqua_cmd_batch.m` and `CFU_cmd_batch.m` behavior before finishing the
GUI. Support recursive input discovery, preset selection, masks, resumable jobs,
progress, structured logs, and deterministic outputs.

Exit gate: a headless run on the reference corpus produces parity artifacts and
can resume safely after interruption.

### Phase 10 — GUI parity

Build the Qt UI over the validated batch API: import, stage controls, overlays,
event viewer, feature visualization, proofreading/filtering, side-by-side
channels, region/landmark tools, CFU viewer, and 3D views. Long-running work must
run outside the UI thread and support cancellation.

Exit gate: scripted acceptance scenarios cover every upstream workflow; GUI
state never changes numerical results.

### Phase 11 — Performance and optional Rust kernels

Benchmark realistic 2D+t and 3D+t datasets for runtime, peak RAM, and output
parity. Optimize in this order:

1. remove accidental copies and improve array layout/chunking;
2. vectorize NumPy/SciPy code;
3. use Numba for simple hot loops;
4. implement isolated Rust kernels with PyO3/maturin;
5. release the GIL and parallelize only where deterministic behavior is kept.

Every Rust kernel must retain the Python reference implementation and run the
same conformance tests.

Exit gate: agreed performance targets pass without weakening parity.

### Phase 12 — Distribution and scientific release

Produce signed wheels/installers for Windows, macOS, and Linux; publish API and
user documentation; archive fixtures and benchmarks; and run reproducibility
tests in CI.

Exit gate: a clean machine can install, reproduce the reference outputs, launch
the GUI, and export results without MATLAB.

## Validation policy

Use multiple levels rather than one global `allclose`:

- **Exact:** masks, labels after canonical relabeling, indexes, event membership,
  CSV categories, and configuration parsing.
- **Tight numeric:** deterministic filtering and transforms, with documented
  `rtol`/`atol` by dtype.
- **Statistical:** fitted models or platform-sensitive solvers, using parameter
  and residual bounds.
- **Structural:** propagation maps and segmentations, using IoU, boundary F1,
  temporal overlap, and feature error together—not IoU alone.
- **End-to-end:** event counts, feature distributions, CFU assignments, runtime,
  and peak memory on real datasets.

CI should run small fixtures on every change and the full MATLAB-versus-Python
corpus on a scheduled or release workflow while MATLAB remains available.

## Immediate next milestone

The next milestone is **not another GUI feature**. It is a reproducible parity
foundation:

1. obtain and pin an AQuA2 commit;
2. run `python tools/inventory_matlab.py /path/to/AQuA2 --output docs/upstream-inventory.json`;
3. create the MATLAB fixture exporter;
4. define canonical array/index contracts;
5. replace the prototype preprocessing stage with fixture-tested `+pre` ports.

Only after this milestone should implementation tickets be estimated.
