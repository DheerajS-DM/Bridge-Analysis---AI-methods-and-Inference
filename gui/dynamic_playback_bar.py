from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QSlider, QLabel, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

class DynamicPlaybackBar(QWidget):
    """Horizontal dynamic playback control bar for time-history simulation scrubbing."""

    stepChanged = pyqtSignal(int)  # emits current frame index

    def __init__(self, parent=None):
        super().__init__(parent)
        self.snapshots = []
        self.current_frame = 0
        self.is_playing = False

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_timer_tick)
        self.timer_interval_ms = 40

        self.setStyleSheet("""
            QWidget {
                background-color: #181825;
                color: #cdd6f4;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 4px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45475a;
                border-color: #89b4fa;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #313244;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #89b4fa;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #cdd6f4;
                width: 14px;
                margin-top: -4px;
                margin-bottom: -4px;
                border-radius: 7px;
            }
            QComboBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 2px 8px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(10)

        self.btn_play = QPushButton("Play")
        self.btn_play.clicked.connect(self.toggle_play)
        layout.addWidget(self.btn_play)

        self.btn_prev = QPushButton("<")
        self.btn_prev.setFixedWidth(28)
        self.btn_prev.clicked.connect(self.step_backward)
        layout.addWidget(self.btn_prev)

        self.btn_next = QPushButton(">")
        self.btn_next.setFixedWidth(28)
        self.btn_next.clicked.connect(self.step_forward)
        layout.addWidget(self.btn_next)

        self.btn_reset = QPushButton("Reset")
        self.btn_reset.clicked.connect(self.reset_playback)
        layout.addWidget(self.btn_reset)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.valueChanged.connect(self._on_slider_changed)
        layout.addWidget(self.slider)

        self.lbl_time = QLabel("t = 0.00 s")
        self.lbl_time.setFixedWidth(75)
        layout.addWidget(self.lbl_time)

        self.lbl_telemetry = QLabel("PGA: 0.00g | Drift: 0.00%")
        self.lbl_telemetry.setStyleSheet("color: #a6adc8; font-size: 11px;")
        layout.addWidget(self.lbl_telemetry)

        self.combo_speed = QComboBox()
        self.combo_speed.addItems(["0.5x", "1.0x", "2.0x"])
        self.combo_speed.setCurrentIndex(1)
        self.combo_speed.currentIndexChanged.connect(self._on_speed_changed)
        layout.addWidget(self.combo_speed)

    def load_snapshots(self, snapshots: list) -> None:
        """Loads discrete time-history dynamic step snapshots."""
        self.snapshots = snapshots
        self.current_frame = 0
        if len(snapshots) > 0:
            self.slider.setRange(0, len(snapshots) - 1)
            self.slider.setValue(0)
            self._update_display(0)
        else:
            self.slider.setRange(0, 0)

    def toggle_play(self) -> None:
        """Toggles between dynamic play and pause."""
        if not self.snapshots:
            return
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.btn_play.setText("Pause")
            self.timer.start(self.timer_interval_ms)
        else:
            self.btn_play.setText("Play")
            self.timer.stop()

    def step_forward(self) -> None:
        if self.snapshots and self.current_frame < len(self.snapshots) - 1:
            self.current_frame += 1
            self.slider.setValue(self.current_frame)

    def step_backward(self) -> None:
        if self.snapshots and self.current_frame > 0:
            self.current_frame -= 1
            self.slider.setValue(self.current_frame)

    def reset_playback(self) -> None:
        self.is_playing = False
        self.timer.stop()
        self.btn_play.setText("Play")
        self.current_frame = 0
        self.slider.setValue(0)

    def _on_timer_tick(self) -> None:
        if not self.snapshots:
            return
        if self.current_frame < len(self.snapshots) - 1:
            self.current_frame += 1
            self.slider.setValue(self.current_frame)
        else:
            self.reset_playback()

    def _on_slider_changed(self, val: int) -> None:
        self.current_frame = val
        self._update_display(val)
        self.stepChanged.emit(val)

    def _update_display(self, idx: int) -> None:
        if 0 <= idx < len(self.snapshots):
            snap = self.snapshots[idx]
            self.lbl_time.setText(f"t = {snap.time_step:.2f} s")
            self.lbl_telemetry.setText(f"Acc: {snap.ground_accel:.3f}g | Drift: {snap.max_drift_ratio*100:.2f}%")

    def _on_speed_changed(self, idx: int) -> None:
        speeds = [80, 40, 20]
        self.timer_interval_ms = speeds[idx] if idx < len(speeds) else 40
        if self.is_playing:
            self.timer.start(self.timer_interval_ms)
