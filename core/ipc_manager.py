import cv2
import numpy as np
import os
import sys

try:
    from multiprocessing import shared_memory
except Exception:
    # python-for-android may be built without POSIX shared memory support
    # (_posixshsem missing). Provide a dummy fallback so the rest of the
    # modules can still be imported on Android.
    shared_memory = None

from core.exception import SharedMemoryError


class SharedMemory:
    shm_map = {}

    @staticmethod
    def _android_stub():
        return hasattr(sys, 'getandroidapilevel') or os.environ.get('P4A_BOOTSTRAP') is not None

    @staticmethod
    def get(name):
        if name not in SharedMemory.shm_map:
            SharedMemory.shm_map[name] = SharedMemory(name)
        return SharedMemory.shm_map[name]

    @staticmethod
    def shm_exists(name):
        return name in SharedMemory.shm_map

    @staticmethod
    def set_data(name, data, size):
        if SharedMemory._android_stub():
            return
        if name not in SharedMemory.shm_map:
            raise SharedMemoryError(f"Shared memory {name} not found")
        shm = SharedMemory.shm_map[name]
        if shm.size < size:
            raise SharedMemoryError(f"Shared memory {name} size {shm.size} not enough for {size}")
        shm.shm.buf[:size] = data

    @staticmethod
    def release(name):
        if name in SharedMemory.shm_map:
            SharedMemory.shm_map[name]._release()
            del SharedMemory.shm_map[name]

    def __init__(self, name):
        self.name = name
        self.size = None
        self.shm = None
        self._init()

    def _init(self):
        if shared_memory is None:
            # On Android we do not use the OCR server shared-memory protocol.
            self.size = 0
            return
        self.shm = shared_memory.SharedMemory(create=False, name=self.name)
        if self.shm is None:
            raise SharedMemoryError(f"Shared memory {self.name} not found")
        self.size = self.shm.size

    def _release(self):
        if self.shm is None:
            return
        self.shm.close()
        self.shm.unlink()
