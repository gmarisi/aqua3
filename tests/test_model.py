from pathlib import Path

from aqua3.config import coerce_parameter_value, load_aqua2_batch_parameters
from aqua3.model import AnalysisConfig, ProjectState


def test_round_trip_state() -> None:
    state = ProjectState(data_path=Path("movie.tif"), output_dir=Path("out"), shape=(100, 64, 64))
    payload = state.to_dict()
    loaded = ProjectState.from_dict(payload)
    assert loaded.data_path == Path("movie.tif")
    assert loaded.output_dir == Path("out")
    assert loaded.shape == (100, 64, 64)


def test_aqua2_aliases_update_matching_fields() -> None:
    config = AnalysisConfig()
    config.temporal_smoothing = 13.2
    config.z_threshold = 4.25
    config.min_event_pixels = 42
    assert config.movAvgWin == 13
    assert config.thrARScl == 4.25
    assert config.minSize == 42


def test_coerce_parameter_value() -> None:
    assert coerce_parameter_value("inf") == float("inf")
    assert coerce_parameter_value("1") == 1
    assert coerce_parameter_value("0.5") == 0.5
    assert coerce_parameter_value("true") is True


def test_load_aqua2_batch_parameters(tmp_path: Path) -> None:
    csv_path = tmp_path / "parameters_for_batch.csv"
    csv_path.write_text(
        "Name,Variable,Type,File1,File2\n"
        "Active voxels threshold scale,thrARScl,activeregion,3,4\n"
        "Minimum duration of signal,minDur,activeregion,5,7\n"
        "Whether need temporal segmentation or not,needTemp,tempSeg,1,0\n",
        encoding="utf-8",
    )
    config = load_aqua2_batch_parameters(csv_path, file_index=2)
    assert config.thrARScl == 4
    assert config.minDur == 7
    assert config.needTemp is False
