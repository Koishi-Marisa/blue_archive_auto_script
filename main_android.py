#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BAAS Android entry point.

This module is invoked from the Android side via Chaquopy. It intentionally
bypasses the PC PyQt GUI and ADB-based device stack, replacing them with
Android-native bridges (screenshot, touch, OCR) injected at runtime.
"""
import os
import sys
import threading
import traceback

# Current BAAS thread instance running on Android.
_thread = None
_thread_lock = threading.Lock()


def _ensure_path():
    """Make sure the app-specific Python root is on sys.path and cwd."""
    app_root = os.path.dirname(os.path.abspath(__file__))
    if app_root not in sys.path:
        sys.path.insert(0, app_root)
    if os.getcwd() != app_root:
        try:
            os.chdir(app_root)
        except Exception:
            pass


def _android_log(msg: str):
    try:
        from android.util import Log
        Log.i("BAAS-Python", msg)
    except Exception:
        print(f"[BAAS-Python] {msg}")


def smoke_test() -> str:
    """Run a minimal import test and return a status string."""
    _ensure_path()
    _android_log("Starting BAAS Android smoke test")

    try:
        import cv2
        import numpy as np
        import requests
        _android_log(f"OpenCV {cv2.__version__}, NumPy {np.__version__}, requests ok")
    except Exception as e:
        _android_log(f"Dependency import failed: {e}")
        return f"dependency_error: {e}"

    try:
        from core.config.config_set import ConfigSet
        from core.Baas_thread import Baas_thread
        _android_log("BAAS core modules imported successfully")
    except Exception as e:
        _android_log(f"BAAS core import failed: {e}")
        return f"baas_import_error: {e}"

    try:
        from core.device import android_bridge
        _android_log("Android bridge module imported successfully")
    except Exception as e:
        _android_log(f"Android bridge import failed: {e}")
        return f"android_bridge_import_error: {e}"

    _android_log("Smoke test passed")
    return "ok"


def _configure_bridge(config):
    """Switch the native bridge to Shizuku if the config requests it."""
    try:
        from java.lang import Class
        bridge = Class.forName("top.qwq123.baas.bridge.BaasBridge")
        screenshot_method = getattr(config, 'screenshot_method', None)
        control_method = getattr(config, 'control_method', None)
        if screenshot_method == 'shizuku' or control_method == 'shizuku':
            bridge.setMode("SHIZUKU")
            _android_log("Native bridge switched to SHIZUKU mode")
        else:
            bridge.setMode("MEDIA_PROJECTION")
            _android_log("Native bridge using MEDIA_PROJECTION mode")
    except Exception as e:
        _android_log(f"Failed to configure bridge mode: {e}")


def _run_task_loop(config_dir: str):
    """Initialize and run the BAAS scheduler loop in a background thread."""
    global _thread
    _ensure_path()
    _android_log(f"run_task called with config_dir={config_dir}")

    try:
        from core.config.config_set import ConfigSet
        config = ConfigSet(config_dir=config_dir)
        _android_log(f"ConfigSet created for {config_dir}")
        _configure_bridge(config)
    except Exception as e:
        _android_log(f"ConfigSet creation failed: {e}")
        with _thread_lock:
            _thread = None
        return

    try:
        from core.Baas_thread import Baas_thread
        thread = Baas_thread(config)
        _android_log("Baas_thread created")
        if not thread.init_all_data():
            _android_log("Baas_thread initialization failed")
            with _thread_lock:
                _thread = None
            return
        _android_log("Baas_thread initialized, starting scheduler")
        with _thread_lock:
            _thread = thread
        thread.thread_starter()
    except Exception as e:
        _android_log(f"Baas_thread run failed: {e}\n{traceback.format_exc()}")
    finally:
        with _thread_lock:
            _thread = None
        _android_log("BAAS task loop ended")


def run_task(config_dir: str) -> str:
    """
    Entry point called by Android when the user starts a task.
    Spawns a background thread that initializes BAAS and runs the scheduler.
    """
    with _thread_lock:
        if _thread is not None:
            return "already_running"

    threading.Thread(target=_run_task_loop, args=(config_dir,), daemon=True).start()
    return "started"


def stop_task() -> str:
    """Signal the running BAAS thread to stop."""
    with _thread_lock:
        if _thread is None:
            return "not_running"
        _thread.flag_run = False
    return "stopping"


def main():
    result = smoke_test()
    _android_log(f"main_android result: {result}")
    return result


if __name__ == "__main__":
    main()
