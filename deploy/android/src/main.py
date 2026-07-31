import sys
import os
import threading
import traceback

# Add the project root to Python path so BAAS modules can be imported
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from PySide6.QtWidgets import (
    QApplication, QLabel, QVBoxLayout, QWidget, QPushButton,
    QTextEdit, QHBoxLayout, QLineEdit
)
from PySide6.QtCore import Qt, QObject, Signal


class LogEmitter(QObject):
    log = Signal(str)


def check_shizuku():
    try:
        from jnius import autoclass
        bridge = autoclass("top.qwq123.baas.bridge.BaasBridge")
        return bridge.diagnosticInfo()
    except Exception as e:
        return f"Shizuku check failed: {e}"


def request_shizuku():
    try:
        from jnius import autoclass
        bridge = autoclass("top.qwq123.baas.bridge.BaasBridge")
        bridge.requestShizukuPermission(8722)
        return "Requested Shizuku permission"
    except Exception as e:
        return f"Request failed: {e}"


def run_shell(command):
    try:
        from jnius import autoclass
        bridge = autoclass("top.qwq123.baas.bridge.BaasBridge")
        return bridge.executeShell(command)
    except Exception as e:
        return f"Shell failed: {e}"


def ensure_android_config():
    """Create or update a minimal Android config set."""
    from core.config.config_set import ConfigSet
    config_dir = "android"
    config_path = f"./config/{config_dir}/config.json"
    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    default = {
        "screenshot_method": "android",
        "control_method": "android",
        "server_mode": "官服",
        "name": "android",
        "priority": "普通",
        "server": "官服",
    }

    import json
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    for key, value in default.items():
        if key not in data:
            data[key] = value

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return ConfigSet(config_dir=config_dir)


def start_baas_task(log_callback):
    def run():
        try:
            log_callback("Ensuring Android config...")
            config = ensure_android_config()

            log_callback("Initializing BAAS Main...")
            from main import Main
            main_instance = Main(ocr_needed=["zh-cn"])

            log_callback("Creating BAAS thread...")
            b_thread = main_instance.get_thread(
                config,
                name="android",
                logger_signal=None,
                button_signal=None,
                update_signal=None,
                exit_signal=None,
            )
            log_callback("Initializing thread data...")
            b_thread.init_all_data()
            log_callback("BAAS ready. Starting explore_activity_mission...")
            b_thread.solve("explore_activity_mission")
            log_callback("Task finished.")
        except Exception as e:
            log_callback("BAAS error:\n" + traceback.format_exc())

    threading.Thread(target=run, daemon=True).start()


def main():
    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle("BAAS on Android")
    layout = QVBoxLayout(window)

    title = QLabel("BAAS PySide6 Android")
    title.setAlignment(Qt.AlignCenter)
    layout.addWidget(title)

    log_box = QTextEdit()
    log_box.setReadOnly(True)
    layout.addWidget(log_box)

    emitter = LogEmitter()
    emitter.log.connect(log_box.append)

    def log(msg):
        emitter.log.emit(msg)

    # Shizuku controls
    shizuku_layout = QHBoxLayout()
    btn_check = QPushButton("Check Shizuku")
    btn_check.clicked.connect(lambda: log(check_shizuku()))
    shizuku_layout.addWidget(btn_check)

    btn_request = QPushButton("Request Shizuku")
    btn_request.clicked.connect(lambda: log(request_shizuku()))
    shizuku_layout.addWidget(btn_request)
    layout.addLayout(shizuku_layout)

    # Shell command
    shell_layout = QHBoxLayout()
    shell_input = QLineEdit()
    shell_input.setPlaceholderText("Shell command (e.g. whoami)")
    shell_layout.addWidget(shell_input)
    btn_shell = QPushButton("Run Shell")
    btn_shell.clicked.connect(lambda: log(run_shell(shell_input.text() or "whoami")))
    shell_layout.addWidget(btn_shell)
    layout.addLayout(shell_layout)

    # BAAS controls
    baas_layout = QHBoxLayout()
    btn_start = QPushButton("Start BAAS")
    btn_start.clicked.connect(lambda: start_baas_task(log))
    baas_layout.addWidget(btn_start)
    layout.addLayout(baas_layout)

    window.show()
    log("UI loaded. Please authorize Shizuku before starting BAAS.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
