from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from analysis.engine import AnalysisEngine
from capture import WindowCapture, find_window
from timing import CandleClock
from ui.overlay import Overlay
from vision.detector import CandleDetector, DetectorConfig


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "Quotex Vision AI - NextGen Trusted"
        )
        self.resize(1100, 760)

        self.cfg = self._load_config()
        self.capture = WindowCapture()
        self.detector = CandleDetector(
            DetectorConfig(
                min_candles=self.cfg["min_candles"],
                max_candles=self.cfg["max_candles"],
                min_body_width_px=self.cfg["min_body_width_px"],
            )
        )
        self.engine = AnalysisEngine()
        self.overlay = Overlay()

        self.running = False
        self.vision_enabled = True
        self.analysis_enabled = True
        self.hwnd = None

        self.clock = CandleClock(30, 0)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.process_once)

        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self.update_clock_display)
        self.ui_timer.start(250)

        self._build_ui()

def _load_config(self):
    # Configuration is intentionally embedded in the application so the
    # installed EXE does not depend on an external config.json file.
    # This makes the Windows installer self-contained.
    return {
        "window_title_contains": "Quotex",
        "capture_fps": 8,
        "overlay_opacity": 0.60,
        "min_candles": 10,
        "max_candles": 30,
        "min_body_width_px": 2,
        "chart_roi": {
            "left": 0.08,
            "top": 0.18,
            "right": 0.98,
            "bottom": 0.96,
        },
        "signal": {
            "min_confidence": 0.66,
            "min_agreement": 0.70,
            "min_direction_edge": 0.12,
        },
    }

    def _build_ui(self):
        central = QWidget()
        root = QVBoxLayout(central)

        title = QLabel(
            "QUOTEX VISION AI — NEXTGEN TRUSTED MODE"
        )
        title.setStyleSheet(
            "font-size: 20px; font-weight: 800;"
        )
        root.addWidget(title)

        self.live_status = QLabel(
            "WAITING FOR QUOTEX"
        )
        self.live_status.setStyleSheet(
            "font-size: 14px; font-weight: 700;"
        )
        root.addWidget(self.live_status)

        controls = QHBoxLayout()

        self.start_btn = QPushButton("START")
        self.start_btn.clicked.connect(self.start)

        self.stop_btn = QPushButton("STOP")
        self.stop_btn.clicked.connect(self.stop)

        controls.addWidget(self.start_btn)
        controls.addWidget(self.stop_btn)

        self.vision_box = QCheckBox(
            "VISIBLE CANDLE BOXES"
        )
        self.vision_box.setChecked(True)
        self.vision_box.stateChanged.connect(
            self._toggle_boxes
        )
        controls.addWidget(self.vision_box)

        self.analysis_box = QCheckBox(
            "ANALYSIS"
        )
        self.analysis_box.setChecked(True)
        controls.addWidget(self.analysis_box)

        controls.addWidget(
            QLabel("Candle:")
        )

        self.timeframe = QComboBox()
        self.timeframe.addItems(
            ["30 seconds", "60 seconds", "120 seconds"]
        )
        self.timeframe.currentIndexChanged.connect(
            self._timeframe_changed
        )
        controls.addWidget(self.timeframe)

        controls.addWidget(
            QLabel("Clock offset:")
        )

        self.offset = QSpinBox()
        self.offset.setRange(-120, 120)
        self.offset.setSuffix(" s")
        self.offset.setValue(0)
        self.offset.valueChanged.connect(
            self._offset_changed
        )
        controls.addWidget(self.offset)

        root.addLayout(controls)

        # Current candle / next prediction card
        top_grid = QGridLayout()

        current_box = QGroupBox(
            "CURRENT CANDLE"
        )
        current_layout = QVBoxLayout(current_box)

        self.current_candle_label = QLabel(
            "Current candle: —"
        )
        self.current_time_label = QLabel(
            "Time: —"
        )
        self.current_remaining_label = QLabel(
            "Remaining: —"
        )
        self.current_direction_label = QLabel(
            "Direction: —"
        )
        self.current_confidence_label = QLabel(
            "Detection confidence: —"
        )

        for label in (
            self.current_candle_label,
            self.current_time_label,
            self.current_remaining_label,
            self.current_direction_label,
            self.current_confidence_label,
        ):
            current_layout.addWidget(label)

        prediction_box = QGroupBox(
            "NEXT CANDLE PREDICTION"
        )
        prediction_layout = QVBoxLayout(prediction_box)

        self.prediction_label = QLabel(
            "NO TRADE"
        )
        self.prediction_label.setStyleSheet(
            "font-size: 28px; font-weight: 900;"
        )
        self.prediction_probability = QLabel(
            "UP — | DOWN —"
        )
        self.prediction_confidence = QLabel(
            "Confidence: —"
        )
        self.prediction_target = QLabel(
            "Target window: —"
        )
        self.prediction_reference = QLabel(
            "Reference: current visible price"
        )

        for label in (
            self.prediction_label,
            self.prediction_probability,
            self.prediction_confidence,
            self.prediction_target,
            self.prediction_reference,
        ):
            prediction_layout.addWidget(label)

        top_grid.addWidget(
            current_box, 0, 0
        )
        top_grid.addWidget(
            prediction_box, 0, 1
        )

        root.addLayout(top_grid)

        # Candle inspection table
        table_box = QGroupBox(
            "DETECTED CANDLES — TRANSPARENT VISION AUDIT"
        )
        table_layout = QVBoxLayout(table_box)

        self.candle_table = QTableWidget(
            0, 9
        )
        self.candle_table.setHorizontalHeaderLabels([
            "#",
            "State",
            "Dir",
            "Vision %",
            "Body",
            "Upper Wick",
            "Lower Wick",
            "Close Pos",
            "Current",
        ])
        self.candle_table.setMaximumHeight(250)
        table_layout.addWidget(
            self.candle_table
        )

        root.addWidget(table_box)

        # Layer audit
        audit_box = QGroupBox(
            "DECISION AUDIT"
        )
        audit_layout = QGridLayout(audit_box)

        self.layer_labels = {}
        names = [
            "L1 Candle Vision",
            "L2 Momentum",
            "L3 Trend",
            "L4 Volatility",
            "L5 Levels",
            "L6 Confirmation",
        ]

        for i, name in enumerate(names):
            name_label = QLabel(name)
            value_label = QLabel("—")
            value_label.setStyleSheet(
                "font-weight: 700;"
            )
            audit_layout.addWidget(
                name_label, i, 0
            )
            audit_layout.addWidget(
                value_label, i, 1
            )
            self.layer_labels[name] = value_label

        root.addWidget(audit_box)

        # Diagnostics
        bottom = QHBoxLayout()

        self.reason_text = QTextEdit()
        self.reason_text.setReadOnly(True)

        self.indicator_text = QTextEdit()
        self.indicator_text.setReadOnly(True)

        bottom.addWidget(
            self.reason_text
        )
        bottom.addWidget(
            self.indicator_text
        )

        root.addLayout(bottom)

        self.setCentralWidget(central)

    def _timeframe_changed(self, index):
        seconds = [30, 60, 120][index]
        self.clock.timeframe_seconds = seconds

    def _offset_changed(self, value):
        self.clock.offset_seconds = value

    def _toggle_boxes(self, state):
        self.vision_enabled = bool(state)
        if not self.vision_enabled:
            self.overlay.hide()
        elif self.running:
            self.overlay.show()

    def start(self):
        self.running = True

        fps = max(
            2,
            int(self.cfg.get("capture_fps", 8))
        )

        self.timer.start(
            max(80, int(1000 / fps))
        )

        self.overlay.show()
        self.live_status.setText(
            "SEARCHING FOR QUOTEX..."
        )

    def stop(self):
        self.running = False
        self.timer.stop()
        self.overlay.hide()

        self.live_status.setText(
            "STOPPED"
        )

    def update_clock_display(self):
        start, end, remaining = (
            self.clock.formatted()
        )

        self.current_time_label.setText(
            f"Window: {start} → {end}"
        )

        self.current_remaining_label.setText(
            f"Seconds remaining: {remaining}"
        )

    def process_once(self):
        if not self.running:
            return

        self.hwnd = find_window(
            self.cfg["window_title_contains"]
        )

        if not self.hwnd:
            self.live_status.setText(
                "QUOTEX WINDOW NOT FOUND"
            )
            return

        try:
            frame, rect = (
                self.capture.capture_window(
                    self.hwnd
                )
            )

            detection = self.detector.detect(
                frame,
                (
                    self.cfg["chart_roi"]["left"],
                    self.cfg["chart_roi"]["top"],
                    self.cfg["chart_roi"]["right"],
                    self.cfg["chart_roi"]["bottom"],
                ),
            )

            signal = None

            if (
                self.analysis_box.isChecked()
                and detection.usable
            ):
                signal = self.engine.analyze(
                    detection.candles,
                    detection.quality,
                    timeframe_minutes=(
                        self.clock.timeframe_seconds / 60.0
                    ),
                    volume_available=(
                        detection.volume_available
                    ),
                    higher_tf_available=(
                        detection.higher_timeframe_available
                    ),
                )

            self._update_current(
                detection
            )

            self._update_prediction(
                detection,
                signal
            )

            self._update_table(
                detection
            )

            self._update_audit(
                signal
            )

            self._update_overlay(
                rect,
                detection,
                signal
            )

            self.live_status.setText(
                "QUOTEX DETECTED • LIVE"
            )

        except Exception as exc:
            self.live_status.setText(
                "VISION ERROR: "
                + type(exc).__name__
            )
            self.reason_text.setPlainText(
                repr(exc)
            )

    def _update_current(self, detection):
        if not detection.candles:
            self.current_candle_label.setText(
                "Current candle: —"
            )
            return

        idx = detection.current_index + 1
        current = detection.candles[
            detection.current_index
        ]

        self.current_candle_label.setText(
            f"Current candle: C{idx} / {len(detection.candles)}"
        )

        direction = (
            "BULL"
            if current.bullish
            else "BEAR"
        )

        self.current_direction_label.setText(
            f"Running direction: {direction}"
        )

        self.current_confidence_label.setText(
            f"Detection confidence: "
            f"{current.confidence*100:.1f}%"
        )

        start, end, remaining = (
            self.clock.formatted()
        )

        self.current_time_label.setText(
            f"Window: {start} → {end}"
        )

        self.current_remaining_label.setText(
            f"Remaining: {remaining}s"
        )

    def _update_prediction(
        self,
        detection,
        signal,
    ):
        start, end, remaining = (
            self.clock.formatted()
        )

        self.prediction_target.setText(
            f"Next window: {end} → "
            f"+{self.clock.timeframe_seconds}s"
        )

        if signal is None:
            self.prediction_label.setText(
                "WAITING FOR VALID DATA"
            )
            self.prediction_probability.setText(
                "UP — | DOWN —"
            )
            self.prediction_confidence.setText(
                "Confidence: —"
            )
            return

        self.prediction_label.setText(
            f"NEXT {self.clock.timeframe_seconds}s: "
            f"{signal.label}"
        )

        self.prediction_probability.setText(
            f"UP {signal.up_probability*100:.1f}% | "
            f"DOWN {signal.down_probability*100:.1f}%"
        )

        self.prediction_confidence.setText(
            f"Confidence: "
            f"{signal.confidence*100:.1f}% | "
            f"Agreement: "
            f"{signal.agreement*100:.1f}%"
        )

        self.reason_text.setPlainText(
            "\n".join(
                signal.reasons
            )
            + "\n\nNO TRADE GATES:\n"
            + (
                "\n".join(
                    signal.no_trade_reasons
                )
                if signal.no_trade_reasons
                else "None"
            )
        )

    def _update_table(self, detection):
        self.candle_table.setRowCount(
            len(detection.candles)
        )

        for r, candle in enumerate(
            detection.candles
        ):
            values = [
                str(r + 1),
                "CURRENT"
                if candle.is_current
                else "CLOSED",
                "BULL"
                if candle.bullish
                else "BEAR",
                f"{candle.confidence*100:.1f}%",
                f"{candle.body_size_px:.1f}",
                f"{candle.upper_wick_px:.1f}",
                f"{candle.lower_wick_px:.1f}",
                f"{candle.close_position:.2f}",
                "YES"
                if candle.is_current
                else "",
            ]

            for c, value in enumerate(
                values
            ):
                item = QTableWidgetItem(
                    value
                )

                if candle.is_current:
                    item.setBackground(
                        QColor(
                            255,
                            205,
                            60,
                            80
                        )
                    )

                self.candle_table.setItem(
                    r, c, item
                )

    def _update_audit(self, signal):
        if signal is None:
            for label in self.layer_labels.values():
                label.setText(
                    "WAITING"
                )
            self.indicator_text.setPlainText(
                "No prediction yet."
            )
            return

        for component in signal.components:
            if component.name in self.layer_labels:
                self.layer_labels[
                    component.name
                ].setText(
                    f"{component.direction} "
                    f"{component.probability_up*100:.1f}%"
                )

        d = getattr(signal, "diagnostics", {}) or {}
        indicators = [
            "The engine predicts DIRECTION, not a guaranteed exact price.",
            "",
            "Reference: CURRENT VISIBLE PRICE",
            f"Prediction window: {self.clock.timeframe_seconds}s",
            "",
            f"RSI: {d.get('rsi')}",
            f"MACD histogram: {d.get('macd_hist')}",
            f"Stochastic K/D: {d.get('stoch_k')} / {d.get('stoch_d')}",
            f"CCI: {d.get('cci')}",
            f"Williams %R: {d.get('williams_r')}",
            f"EMA 9/21/50/200: {d.get('ema9')} / {d.get('ema21')} / {d.get('ema50')} / {d.get('ema200')}",
            f"ADX: {d.get('adx')}",
            f"Volatility: {d.get('volatility_regime')}",
            f"Support/Resistance: {d.get('support')} / {d.get('resistance')}",
            f"VWAP: {d.get('vwap')}",
            f"Fib 38.2/50/61.8: {d.get('fib_382')} / {d.get('fib_500')} / {d.get('fib_618')}",
            f"Pivot/R1/S1: {d.get('pivot')} / {d.get('pivot_r1')} / {d.get('pivot_s1')}",
            f"Structure: {d.get('structure')}",
        ]

        self.indicator_text.setPlainText(
            "\n".join(indicators)
        )

    def _update_overlay(
        self,
        rect,
        detection,
        signal,
    ):
        left, top, right, bottom = rect

        boxes = []
        for candle in detection.candles:
            x = int(candle.body_left - left)
            y = int(candle.body_top - top)
            w = max(
                2,
                int(
                    candle.body_right
                    - candle.body_left
                    + 1
                ),
            )
            h = max(
                3,
                int(
                    candle.body_bottom
                    - candle.body_top
                    + 1
                ),
            )

            boxes.append(
                (
                    x, y, w, h,
                    candle.confidence,
                    candle.is_current,
                )
            )

        if signal is None:
            label = "SCAN"
            p = 0.50
            c = 0.0
            status = (
                f"{len(detection.candles)} candles | "
                f"Vision {detection.quality*100:.0f}%"
            )
        else:
            label = signal.label
            p = signal.up_probability
            c = signal.confidence
            status = (
                f"NEXT {signal.horizon_seconds}s | "
                f"Vision {detection.quality*100:.0f}% | "
                f"Agreement {signal.agreement*100:.0f}%"
            )

        self.overlay.setGeometry(
            left,
            top,
            max(1, right - left),
            max(1, bottom - top),
        )

        self.overlay.set_data(
            boxes,
            label,
            p,
            c,
            status,
            current_index=detection.current_index,
        )

        if self.vision_enabled:
            self.overlay.show()

    def closeEvent(self, event):
        self.stop()
        event.accept()
