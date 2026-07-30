#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BAAS Android entry point.

This module is invoked from the Android side via Chaquopy. It intentionally
bypasses the PC PyQt GUI and ADB-based device stack, replacing them with
Android-native bridges (screenshot, touch, OCR) injected at runtime.

Current implementation is a minimal smoke test: it reports the Python version,
imports core BAAS modules, and exposes a hook for the Android UI.
"""
import importlib
import os
import sys
import time


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
        # These import paths assume main_android.py lives next to core/ and module/
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


def run_task(config_dir: str) -> str:
    """
    Entry point called by Android when the user starts a task.
    It creates a minimal BAAS thread using the Android screenshot/control bridge.
    """
    _ensure_path()
    _android_log(f"run_task called with config_dir={config_dir}")

    try:
        from core.config.config_set import ConfigSet
        config = ConfigSet(config_dir=config_dir)
        _android_log(f"ConfigSet created for {config_dir}")
    except Exception as e:
        _android_log(f"ConfigSet creation failed: {e}")
        return f"config_error: {e}"

    try:
        from core.Baas_thread import Baas_thread
        thread = Baas_thread(config)
        _android_log("Baas_thread created")
        if not thread.init_all_data():
            return "init_failed"
        _android_log("Baas_thread initialized")
        return "ok"
    except Exception as e:
        _android_log(f"Baas_thread init failed: {e}")
        return f"thread_error: {e}"


def main():
    result = smoke_test()
    _android_log(f"main_android result: {result}")
    return result


if __name__ == "__main__":
    main()
