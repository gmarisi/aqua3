from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_conda_environment_installs_project_with_dev_dependencies() -> None:
    environment = (ROOT / "environment.yml").read_text(encoding="utf-8")
    assert "name: aqua3" in environment
    assert "python=3.11" in environment
    assert "- -e .[dev]" in environment


def test_local_setup_scripts_install_and_check_aqua3() -> None:
    for relative_path in ("scripts/setup-env.sh", "scripts/setup-env.ps1"):
        script = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "pip install" in script
        assert "aqua3 --check" in script
