#!/usr/bin/env python3
"""Inventory an AQuA2 MATLAB checkout for port-planning purposes."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Sequence

FUNCTION_RE = re.compile(r"^\s*function\s+(?:\[[^]]*\]|\w+)\s*=\s*(\w+)|^\s*function\s+(\w+)", re.MULTILINE)
MEX_SUFFIXES = (".mexw64", ".mexa64", ".mexmaci64", ".mexmaca64")


def matlab_package(path: Path, root: Path) -> str | None:
    parts = path.relative_to(root).parts[:-1]
    packages = [part[1:] for part in parts if part.startswith("+")]
    return ".".join(packages) or None


def first_function(source: str) -> str | None:
    match = FUNCTION_RE.search(source)
    if match is None:
        return None
    return match.group(1) or match.group(2)


def inventory(root: Path) -> dict[str, object]:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"AQuA2 checkout is not a directory: {root}")

    matlab_files: list[dict[str, object]] = []
    package_counts: Counter[str] = Counter()
    for path in sorted(root.rglob("*.m")):
        source = path.read_text(encoding="utf-8", errors="replace")
        package = matlab_package(path, root)
        package_counts[package or "(root)"] += 1
        matlab_files.append(
            {
                "path": path.relative_to(root).as_posix(),
                "package": package,
                "function": first_function(source),
                "lines": source.count("\n") + bool(source),
            }
        )

    native_files = [
        path.relative_to(root).as_posix()
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name.lower().endswith(MEX_SUFFIXES)
    ]
    return {
        "root": str(root),
        "matlab_file_count": len(matlab_files),
        "matlab_line_count": sum(int(item["lines"]) for item in matlab_files),
        "package_counts": dict(sorted(package_counts.items())),
        "native_file_count": len(native_files),
        "native_files": native_files,
        "matlab_files": matlab_files,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="path to the upstream AQuA2 checkout")
    parser.add_argument("--output", type=Path, help="write JSON to this path instead of stdout")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = inventory(args.root)
    except ValueError as exc:
        build_parser().error(str(exc))
    payload = json.dumps(report, indent=2) + "\n"
    if args.output is None:
        print(payload, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
