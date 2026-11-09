"""Command-line entry point for launching and diagnosing AQuA3."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Sequence

from . import __version__

RUNTIME_DEPENDENCIES = {
    "numpy": "NumPy",
    "tifffile": "tifffile",
    "PySide6": "PySide6",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aqua3",
        description="Launch the AQuA3 desktop application.",
    )
    parser.add_argument(
        "data",
        nargs="?",
        type=Path,
        help="optional TIFF stack to open when the GUI starts",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="check whether GUI runtime dependencies are installed and exit",
    )
    parser.add_argument("--version", action="version", version=f"AQuA3 {__version__}")
    return parser


def dependency_status() -> dict[str, bool]:
    return {
        display_name: importlib.util.find_spec(module_name) is not None
        for module_name, display_name in RUNTIME_DEPENDENCIES.items()
    }


def print_dependency_check() -> bool:
    status = dependency_status()
    print(f"AQuA3 {__version__} runtime check")
    for name, available in status.items():
        marker = "OK" if available else "MISSING"
        print(f"  [{marker}] {name}")
    if not all(status.values()):
        print("\nInstall the application with: python -m pip install -e .")
        return False
    print("\nAQuA3 is ready. Launch it with: aqua3")
    return True


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.check:
        return 0 if print_dependency_check() else 1

    missing = [name for name, available in dependency_status().items() if not available]
    if missing:
        print(
            "AQuA3 cannot start because these dependencies are missing: "
            + ", ".join(missing),
            file=sys.stderr,
        )
        print("Run: python -m pip install -e .", file=sys.stderr)
        return 1

    from .app import main as run_gui

    return run_gui(args.data)


if __name__ == "__main__":
    raise SystemExit(main())
