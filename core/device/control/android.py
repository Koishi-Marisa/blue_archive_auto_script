# -*- coding: utf-8 -*-
"""Android touch control adapter for BAAS."""
from core.device.android_bridge import click, swipe, long_click


class AndroidControl:
    def __init__(self, connection=None):
        self.connection = connection

    def click(self, x, y):
        click(x, y)

    def swipe(self, x1, y1, x2, y2, duration):
        swipe(x1, y1, x2, y2, duration)

    def long_click(self, x, y, duration):
        long_click(x, y, duration)

    def scroll(self, x, y, clicks):
        # Map scroll to small vertical swipes.
        step = 50 * (1 if clicks > 0 else -1)
        for _ in range(abs(clicks)):
            swipe(x, y, x, y - step, 100)
