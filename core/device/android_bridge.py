# -*- coding: utf-8 -*-
"""
BAAS Android bridge.

This module is loaded only on Android (via Chaquopy). It provides screenshot,
touch control and OCR by calling back into the Kotlin BaasBridge object.
"""
import io
import json
from typing import Optional, Tuple

import cv2
import numpy as np


def _bridge():
    """Return the BaasBridge Java/Kotlin class."""
    try:
        # Chaquopy path
        from com.chaquo.python import Python
        from java.lang import Class
        return Class.forName("top.qwq123.baas.bridge.BaasBridge")
    except Exception:
        pass
    try:
        # python-for-android / pyjnius path
        from jnius import autoclass
        return autoclass("top.qwq123.baas.bridge.BaasBridge")
    except Exception as e:
        raise RuntimeError("BaasBridge not available") from e


def screenshot() -> Optional[np.ndarray]:
    """Return the current screenshot as a BGR numpy array, or None."""
    bridge = _bridge()
    jpeg = bridge.screenshotJpeg()
    if jpeg is None:
        return None
    data = bytes(jpeg)
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img


def screenshot_size() -> Optional[Tuple[int, int]]:
    """Return (width, height) of the last screenshot."""
    bridge = _bridge()
    size = bridge.screenshotSize()
    if not size:
        return None
    w, h = size.split(",")
    return int(w), int(h)


def click(x: int, y: int) -> bool:
    return _bridge().click(int(x), int(y))


def swipe(x1: int, y1: int, x2: int, y2: int, duration: int = 300) -> bool:
    return _bridge().swipe(int(x1), int(y1), int(x2), int(y2), int(duration))


def long_click(x: int, y: int, duration: int = 1000) -> bool:
    return _bridge().longClick(int(x), int(y), int(duration))


def ocr(image: np.ndarray, language: str = "zh-cn") -> list:
    """
    Run on-device OCR on the given BGR image.
    Returns a list of dicts: {"text": str, "box": [(x,y),...], "score": float}.
    """
    bridge = _bridge()
    success, buf = cv2.imencode(".png", image)
    if not success:
        return []
    data = bytes(buf)
    h, w = image.shape[:2]
    result_json = bridge.ocr(data, w, h, language)
    return json.loads(result_json)


class AndroidBridge:
    """Convenience wrapper used by Screenshot/Control adapters."""

    def screenshot(self):
        return screenshot()

    def click(self, x, y):
        return click(x, y)

    def swipe(self, x1, y1, x2, y2, duration):
        return swipe(x1, y1, x2, y2, duration)

    def long_click(self, x, y, duration):
        return long_click(x, y, duration)
