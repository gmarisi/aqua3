from pathlib import Path

from tools.inventory_matlab import first_function, inventory, matlab_package


def test_first_function_supports_output_and_no_output_forms() -> None:
    assert first_function("function value = calculate(input)\n") == "calculate"
    assert first_function("function run_pipeline(options)\n") == "run_pipeline"
    assert first_function("% script only\nvalue = 1;\n") is None


def test_inventory_groups_packages_and_native_files(tmp_path: Path) -> None:
    package = tmp_path / "src" / "+pre"
    package.mkdir(parents=True)
    (package / "baseline.m").write_text(
        "function result = baseline(movie)\nresult = movie;\n",
        encoding="utf-8",
    )
    (tmp_path / "aqua_gui.m").write_text("function aqua_gui\n", encoding="utf-8")
    native = tmp_path / "BILCO" / "solver.mexa64"
    native.parent.mkdir()
    native.write_bytes(b"native")

    report = inventory(tmp_path)

    assert report["matlab_file_count"] == 2
    assert report["package_counts"] == {"(root)": 1, "pre": 1}
    assert report["native_files"] == ["BILCO/solver.mexa64"]
    files = {item["path"]: item for item in report["matlab_files"]}
    assert files["src/+pre/baseline.m"]["function"] == "baseline"
    assert matlab_package(package / "baseline.m", tmp_path) == "pre"
