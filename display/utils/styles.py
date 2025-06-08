"""
Stylesheet definitions for the display system.
"""


def get_application_stylesheet() -> str:
    """Get the complete application stylesheet."""
    return """
        QMainWindow {
            background-color: #111827;
        }
        QWidget {
            background-color: #111827;
            color: #e5e7eb;
        }
        QLabel {
            color: #e5e7eb;
            font-size: 12px;
            padding: 0;
            background: transparent;
        }
        QLabel[heading="true"] {
            font-size: 14px;
            font-weight: bold;
            color: #f3f4f6;
            padding: 8px;
            background-color: #1f2937;
            border-radius: 4px;
            margin-bottom: 4px;
        }
        QFrame {
            background-color: #1f2937;
            border: 1px solid #374151;
            border-radius: 6px;
            padding: 4px;
        }
        QFrame[panel="true"] {
            margin: 4px;
            padding: 8px;
        }
        QPushButton {
            background-color: #3b82f6;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            color: white;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #2563eb;
        }
        QProgressBar {
            border: 1px solid #374151;
            border-radius: 4px;
            text-align: center;
            height: 6px;
        }
        QProgressBar::chunk {
            background-color: #3b82f6;
            border-radius: 3px;
        }
        QScrollArea {
            border: none;
            background: transparent;
        }
        QScrollBar:vertical {
            border: none;
            background: #1f2937;
            width: 8px;
            border-radius: 4px;
        }
        QScrollBar::handle:vertical {
            background: #4b5563;
            border-radius: 4px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            border: none;
            background: none;
        }
        QSplitter::handle {
            background-color: #374151;
            width: 1px;
        }
        QChartView {
            background-color: #1f2937;
            border-radius: 6px;
        }
        TimelineWidget {
            max-height: 120px;
            background-color: #1f2937;
            border-radius: 6px;
            border: 1px solid #374151;
        }
        QLineEdit {
            background-color: #1f2937;
            border: 1px solid #374151;
            border-radius: 4px;
            padding: 6px;
            color: #e5e7eb;
        }
        QLineEdit:focus {
            border-color: #3b82f6;
        }
    """