import sys
import os

# Add the project root to Python path so BAAS modules can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QPushButton
from PySide6.QtCore import Qt


def main():
    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle("BAAS on Android")
    layout = QVBoxLayout(window)

    label = QLabel("BAAS PySide6 Android Minimal UI")
    label.setAlignment(Qt.AlignCenter)
    layout.addWidget(label)

    btn = QPushButton("Click Me")
    btn.clicked.connect(lambda: label.setText("Button clicked!"))
    layout.addWidget(btn)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
