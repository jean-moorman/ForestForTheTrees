"""
Prompt interface for user task input.
"""
from typing import Optional

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton
from PyQt6.QtCore import pyqtSignal


class PromptInterface(QWidget):
    """Interface for user task prompts."""
    
    prompt_submitted = pyqtSignal(str)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.prompt_input = QLineEdit()
        self.prompt_input.setPlaceholderText("Enter your task prompt...")
        
        self.submit_button = QPushButton("Submit")
        self.submit_button.setEnabled(False)
        
        layout.addWidget(self.prompt_input)
        layout.addWidget(self.submit_button)

    def _connect_signals(self) -> None:
        """Connect signal handlers."""
        self.prompt_input.textChanged.connect(self._handle_input_change)
        self.prompt_input.returnPressed.connect(self._handle_submit)
        self.submit_button.clicked.connect(self._handle_submit)

    def _handle_input_change(self, text: str) -> None:
        """Enable/disable submit button based on input."""
        self.submit_button.setEnabled(bool(text.strip()))

    def _handle_submit(self) -> None:
        """Handle prompt submission."""
        text = self.prompt_input.text().strip()
        if text:
            self.prompt_submitted.emit(text)
            self.prompt_input.clear()
            self.setEnabled(False)

    def reset(self) -> None:
        """Reset interface after processing."""
        self.setEnabled(True)
        self.prompt_input.setFocus()