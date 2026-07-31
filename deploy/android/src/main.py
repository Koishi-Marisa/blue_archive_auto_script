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
    """Persist text to a file in the private files directory."""
    try:
        path = os.path.join(_ANDROID_PRIVATE, name)
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

# p4a keeps the working directory at the app root (where main.py and config/
# live). Do NOT change it here, otherwise relative paths like config/static.json
# break. Use ANDROID_PRIVATE only for writable logs.
_ANDROID_PRIVATE = os.environ.get('ANDROID_PRIVATE')
if not _ANDROID_PRIVATE or not os.path.isdir(_ANDROID_PRIVATE):
    _ANDROID_PRIVATE = os.getcwd()
_log(f"ANDROID_PRIVATE={_ANDROID_PRIVATE}")

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
    """Create or update the Android config set.

    The repository ships a complete default config under config/android/config.json.
    If the runtime copy is missing, copy that template; otherwise only update the
    Android-specific screenshot/control methods so the dataclass stays valid.
    """
    import json
    import shutil
    from core.config.config_set import ConfigSet

    config_dir = "android"
    config_path = os.path.join(os.getcwd(), "config", config_dir, "config.json")
    template_path = os.path.join(os.getcwd(), "config", config_dir, "config.json")

    # The template lives in the same relative path inside the APK. If it exists
    # but the writable runtime copy does not, copy the whole template to avoid
    # creating an incomplete config that breaks ConfigSet's dataclass.
    if not os.path.exists(config_path) and os.path.exists(template_path):
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        shutil.copyfile(template_path, config_path)

    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        # Fallback: an extremely small subset is not enough for Config, so raise
        # early with a clear message instead of crashing inside ConfigSet.
        raise FileNotFoundError(
            f"Android config template not found: {template_path}"
        )

    # Override only the Android-specific fields; keep every other field intact.
    data["screenshot_method"] = "shizuku"
    data["control_method"] = "shizuku"
    if "server" not in data:
        data["server"] = "官服"
    if "name" not in data:
        data["name"] = "android"

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
