from aqua3 import __version__
from aqua3.__main__ import build_parser, dependency_status, main


def test_parser_accepts_optional_tiff() -> None:
    args = build_parser().parse_args(["movie.tif"])
    assert args.data.name == "movie.tif"
    assert args.check is False


def test_version_is_exposed() -> None:
    assert __version__ == "0.2.0"


def test_dependency_status_has_expected_runtime_packages() -> None:
    assert set(dependency_status()) == {"NumPy", "tifffile", "PySide6"}


def test_check_returns_result_matching_dependencies(capsys) -> None:
    status = dependency_status()
    expected = 0 if all(status.values()) else 1
    assert main(["--check"]) == expected
    assert f"AQuA3 {__version__} runtime check" in capsys.readouterr().out
