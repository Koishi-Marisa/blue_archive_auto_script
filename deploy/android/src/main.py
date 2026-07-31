import os
import sys
import traceback


def _android_log(tag, message):
    """Write to Android logcat via jnius when available."""
    try:
        from jnius import autoclass
        Log = autoclass("android.util.Log")
        Log.i(tag, str(message))
    except Exception:
        pass


def _write_file(name, text):
    """Persist text to a file in the current working directory."""
    try:
        path = os.path.join(os.getcwd(), name)
        with open(path, 'a', encoding='utf-8') as f:
            f.write(text)
            f.write('\n')
    except Exception:
        pass


def _log(msg):
    _android_log("BAAS_UI", msg)


# Record startup diagnostics as early as possible.
_log("main.py module loaded")
_log(f"cwd={os.getcwd()}")
_log(f"ANDROID_PRIVATE={os.environ.get('ANDROID_PRIVATE')}")
_log(f"ANDROID_ARGUMENT={os.environ.get('ANDROID_ARGUMENT')}")
_log(f"ANDROID_ENTRYPOINT={os.environ.get('ANDROID_ENTRYPOINT')}")
_log(f"ANDROID_UNPACK={os.environ.get('ANDROID_UNPACK')}")

# On Android, p4a launches the app with ANDROID_PRIVATE set to the app's
# private files directory. Make that the working directory so config/logs
# are written somewhere writable.
_ANDROID_PRIVATE = os.environ.get('ANDROID_PRIVATE')
if _ANDROID_PRIVATE and os.path.isdir(_ANDROID_PRIVATE):
    os.chdir(_ANDROID_PRIVATE)
    _log(f"changed cwd to {os.getcwd()}")

# Add the project root to Python path so BAAS modules can be imported.
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


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
    import json
    from core.config.config_set import ConfigSet

    config_dir = "android"
    config_path = os.path.join(os.getcwd(), "config", config_dir, "config.json")
    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    default = {
        "screenshot_method": "android",
        "control_method": "android",
        "server_mode": "官服",
        "name": "android",
        "priority": "普通",
        "server": "官服",
    }

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
    import threading

    def run():
        try:
            log_callback("Ensuring Android config...")
            config = ensure_android_config()

            log_callback("Initializing BAAS Main...")
            from baas_main import Main
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
        except Exception:
            log_callback("BAAS error:\n" + traceback.format_exc())

    threading.Thread(target=run, daemon=True).start()


def main():
    """Application entry point invoked by python-for-android Qt bootstrap.

    PySide6/Qt imports are deferred until this function to avoid initializing
    Qt before the bootstrap has finished setting up the Qt main loop.
    """
    _log("main() started")

    # Force the Android platform plugin and avoid picking up a desktop plugin.
    os.environ.setdefault("QT_QPA_PLATFORM", "android")
    _log("QT_QPA_PLATFORM=" + os.environ.get("QT_QPA_PLATFORM", "<not set>"))

    _log("Importing PySide6.QtCore...")
    from PySide6.QtCore import Qt, QObject, Signal, QCoreApplication
    _log("Importing PySide6.QtWidgets...")
    from PySide6.QtWidgets import (
        QApplication, QLabel, QVBoxLayout, QWidget, QPushButton,
        QTextEdit, QHBoxLayout, QLineEdit
    )
    _log("PySide6 imports complete")

    class LogEmitter(QObject):
        log = Signal(str)

    _log("Checking existing QApplication instance...")
    app = QApplication.instance()
    if app is None:
        _log("Creating new QApplication...")
        app = QApplication(sys.argv)
    else:
        _log("Reusing existing QApplication instance")

    _log("Creating main window...")
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
        text = str(msg)
        emitter.log.emit(text)
        _android_log("BAAS_UI", text)

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
    _log("Entering QApplication event loop...")
    return app.exec()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        exc = traceback.format_exc()
        _write_file('crash.log', exc)
        _android_log("BAAS_CRASH", exc)
        # Do not re-raise: a Python exception here would propagate through
        # PyRun_SimpleFile and can cause the p4a C bootstrap to crash.
        # Returning a non-zero status is enough to report failure.
        sys.exit(1)
