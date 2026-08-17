from __future__ import annotations

from typing import Iterable, Tuple

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget


class Overlay(QWidget):
    def __init__(self):
        super().__init__()

        self.boxes = []
        self.signal_text = "NO TRADE"
        self.signal_probability = 50.0
        self.confidence = 0.0
        self.status = "WAITING"
        self.current_index = -1

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowDoesNotAcceptFocus
        )

        self.setAttribute(
            Qt.WA_TranslucentBackground,
            True,
        )

        self.setAttribute(
            Qt.WA_TransparentForMouseEvents,
            True,
        )

    def set_data(
        self,
        boxes: Iterable[Tuple],
        label,
        probability,
        confidence,
        status,
        current_index=-1,
    ):
        self.boxes = list(boxes)
        self.signal_text = label
        self.signal_probability = probability
        self.confidence = confidence
        self.status = status
        self.current_index = current_index
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.Antialiasing
        )

        # DETECTED CANDLE BOXES
        for i, item in enumerate(self.boxes):
            x, y, w, h, conf, is_current = item

            if is_current:
                color = QColor(
                    255, 205, 40, 240
                )
                width = 3
            else:
                color = QColor(
                    0, 220, 155, 180
                )
                width = 2

            pen = QPen(color)
            pen.setWidth(width)
            painter.setPen(pen)
            painter.drawRect(
                x, y, w, h
            )

            # Confidence above each candle.
            painter.setFont(
                QFont(
                    "Segoe UI",
                    8,
                    QFont.Bold
                )
            )

            painter.setPen(
                QColor(
                    255,
                    255,
                    255,
                    220
                )
            )

            painter.drawText(
                x,
                max(14, y - 3),
                f"C{i+1} {conf*100:.0f}%"
            )

            if is_current:
                painter.setPen(
                    QColor(
                        255,
                        205,
                        40,
                        245
                    )
                )
                painter.drawText(
                    x,
                    y + h + 13,
                    "CURRENT"
                )

        # BIG TRUST PANEL
        width = min(
            500,
            max(320, self.width() - 20)
        )

        painter.setPen(Qt.NoPen)

        painter.setBrush(
            QColor(
                4,
                15,
                24,
                170
            )
        )

        painter.drawRoundedRect(
            10,
            10,
            width,
            112,
            12,
            12
        )

        painter.setPen(
            QColor(
                255,
                255,
                255,
                240
            )
        )

        painter.setFont(
            QFont(
                "Segoe UI",
                11,
                QFont.Bold
            )
        )

        painter.drawText(
            24,
            31,
            "QUOTEX VISION AI • LIVE AUDIT"
        )

        signal_color = QColor(
            255,
            200,
            40,
            245
        )

        if self.signal_text == "UP":
            signal_color = QColor(
                30,
                230,
                145,
                250
            )

        elif self.signal_text == "DOWN":
            signal_color = QColor(
                255,
                90,
                105,
                250
            )

        painter.setPen(
            signal_color
        )

        painter.setFont(
            QFont(
                "Segoe UI",
                19,
                QFont.Bold
            )
        )

        painter.drawText(
            24,
            61,
            f"NEXT: {self.signal_text}"
        )

        painter.setPen(
            QColor(
                255,
                255,
                255,
                230
            )
        )

        painter.setFont(
            QFont(
                "Segoe UI",
                10
            )
        )

        painter.drawText(
            180,
            57,
            f"UP {self.signal_probability*100:.1f}%"
        )

        painter.drawText(
            180,
            76,
            f"CONF {self.confidence*100:.0f}%"
        )

        painter.drawText(
            24,
            98,
            self.status[:72]
        )
