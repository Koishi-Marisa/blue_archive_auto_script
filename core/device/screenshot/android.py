# -*- coding: utf-8 -*-
"""Android screenshot adapter for BAAS."""
from core.device.android_bridge import screenshot


class AndroidScreenshot:
    def __init__(self, connection=None):
        self.connection = connection

    def screenshot(self):
        return screenshot()
