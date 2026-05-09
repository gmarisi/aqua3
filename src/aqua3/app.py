from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .config import load_aqua2_batch_parameters
from .io import load_tiff_stack, save_detection_outputs
from .model import ProjectState
from .pipeline import AquaPipeline, PipelineResult


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AQuA3 - Python AQuA2 Port")
        self.resize(1040, 720)

        self.state = ProjectState()
        self.stack: np.ndarray | None = None
        self.result: PipelineResult | None = None

        root = QWidget()
        layout = QVBoxLayout(root)

        self.info_label = QLabel("No dataset loaded")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.info_label)

        tabs = QTabWidget()
        tabs.addTab(self._build_data_tab(), "Data")
        tabs.addTab(self._build_detection_tab(), "Detection")
        tabs.addTab(self._build_export_tab(), "Export")
        layout.addWidget(tabs)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

        self.setCentralWidget(root)

    def _build_data_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        actions = QHBoxLayout()
        self.load_btn = QPushButton("Load TIFF stack")
        self.load_btn.clicked.connect(self.load_data)
        self.load_params_btn = QPushButton("Load AQuA2 batch CSV")
        self.load_params_btn.clicked.connect(self.load_parameters)
        actions.addWidget(self.load_btn)
        actions.addWidget(self.load_params_btn)
        layout.addLayout(actions)

        parameters = QFormLayout()
        self.file_index = QSpinBox()
        self.file_index.setRange(1, 999)
        self.file_index.setValue(1)
        parameters.addRow("AQuA2 FileN column", self.file_index)
        layout.addLayout(parameters)
        layout.addStretch(1)
        return tab

    def _build_detection_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        preprocessing = QGroupBox("Preprocessing / dF")
        pre_form = QFormLayout(preprocessing)
        self.mov_avg = QSpinBox()
        self.mov_avg.setRange(1, 2000)
        self.mov_avg.setValue(self.state.config.movAvgWin)
        self.med_smo = QSpinBox()
        self.med_smo.setRange(0, 5)
        self.med_smo.setValue(self.state.config.medSmo)
        self.var_est = QDoubleSpinBox()
        self.var_est.setDecimals(5)
        self.var_est.setRange(0.00001, 10.0)
        self.var_est.setValue(self.state.config.varEst)
        pre_form.addRow("Baseline window (movAvgWin)", self.mov_avg)
        pre_form.addRow("Median radius (medSmo)", self.med_smo)
        pre_form.addRow("Noise variance fallback (varEst)", self.var_est)
        layout.addWidget(preprocessing)

        active = QGroupBox("Active region / event constraints")
        active_form = QFormLayout(active)
        self.thr_ar = QDoubleSpinBox()
        self.thr_ar.setRange(0.1, 25.0)
        self.thr_ar.setValue(self.state.config.thrARScl)
        self.min_dur = QSpinBox()
        self.min_dur.setRange(1, 10000)
        self.min_dur.setValue(self.state.config.minDur)
        self.min_size = QSpinBox()
        self.min_size.setRange(1, 10_000_000)
        self.min_size.setValue(self.state.config.minSize)
        self.frame_rate = QDoubleSpinBox()
        self.frame_rate.setRange(0.0001, 10000.0)
        self.frame_rate.setValue(self.state.config.frameRate)
        self.spatial_res = QDoubleSpinBox()
        self.spatial_res.setRange(0.0001, 10000.0)
        self.spatial_res.setValue(self.state.config.spatialRes)
        active_form.addRow("Threshold scale (thrARScl)", self.thr_ar)
        active_form.addRow("Minimum duration (minDur)", self.min_dur)
        active_form.addRow("Minimum size (minSize)", self.min_size)
        active_form.addRow("Frame rate", self.frame_rate)
        active_form.addRow("Spatial resolution", self.spatial_res)
        layout.addWidget(active)

        self.run_btn = QPushButton("Run AQuA2-style detection")
        self.run_btn.clicked.connect(self.run_analysis)
        layout.addWidget(self.run_btn)
        layout.addStretch(1)
        return tab

    def _build_export_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.save_project_btn = QPushButton("Save project JSON")
        self.save_project_btn.clicked.connect(self.save_project)
        self.save_outputs_btn = QPushButton("Save detection outputs")
        self.save_outputs_btn.clicked.connect(self.save_outputs)
        layout.addWidget(self.save_project_btn)
        layout.addWidget(self.save_outputs_btn)
        layout.addStretch(1)
        return tab

    def load_data(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open TIFF", "", "TIFF (*.tif *.tiff)")
        if not path:
            return
        stack = load_tiff_stack(Path(path))
        self.stack = stack
        self.state.data_path = Path(path)
        self.state.shape = stack.shape
        self.info_label.setText(f"Loaded: {path} | shape={stack.shape}")
        self.log.append(f"Loaded dataset with shape {stack.shape}")

    def load_parameters(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open AQuA2 batch parameters", "", "CSV (*.csv)")
        if not path:
            return
        self.state.config = load_aqua2_batch_parameters(Path(path), self.file_index.value())
        self._sync_config_to_widgets()
        self.log.append(f"Loaded AQuA2 parameters from {path} (File{self.file_index.value()})")

    def run_analysis(self) -> None:
        if self.stack is None:
            QMessageBox.warning(self, "No data", "Please load a TIFF stack first.")
            return

        self._sync_widgets_to_config()
        pipeline = AquaPipeline(self.state.config)
        self.result = pipeline.run(self.stack)

        event_voxels = int(self.result.events_mask.sum())
        event_count = len(self.result.events)
        self.log.append(
            "AQuA2-style detection complete: "
            f"events={event_count}, active_voxels={event_voxels}, "
            f"score_map={self.result.score_map.shape}"
        )

    def save_project(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save Project", "project.json", "JSON (*.json)")
        if not path:
            return
        with Path(path).open("w", encoding="utf-8") as handle:
            json.dump(self.state.to_dict(), handle, indent=2)
        self.log.append(f"Saved project state to {path}")

    def save_outputs(self) -> None:
        if self.result is None:
            QMessageBox.warning(self, "No results", "Run detection before exporting outputs.")
            return
        output_dir = QFileDialog.getExistingDirectory(self, "Select output directory")
        if not output_dir:
            return
        stem = self.state.data_path.stem if self.state.data_path else "aqua3_result"
        self.state.output_dir = Path(output_dir)
        save_detection_outputs(Path(output_dir), stem, self.result)
        self.log.append(f"Saved event table and arrays to {output_dir}")

    def _sync_widgets_to_config(self) -> None:
        self.state.config.movAvgWin = self.mov_avg.value()
        self.state.config.medSmo = self.med_smo.value()
        self.state.config.varEst = self.var_est.value()
        self.state.config.thrARScl = self.thr_ar.value()
        self.state.config.minDur = self.min_dur.value()
        self.state.config.minSize = self.min_size.value()
        self.state.config.frameRate = self.frame_rate.value()
        self.state.config.spatialRes = self.spatial_res.value()

    def _sync_config_to_widgets(self) -> None:
        self.mov_avg.setValue(self.state.config.movAvgWin)
        self.med_smo.setValue(self.state.config.medSmo)
        self.var_est.setValue(self.state.config.varEst)
        self.thr_ar.setValue(self.state.config.thrARScl)
        self.min_dur.setValue(self.state.config.minDur)
        self.min_size.setValue(self.state.config.minSize)
        self.frame_rate.setValue(self.state.config.frameRate)
        self.spatial_res.setValue(self.state.config.spatialRes)


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
