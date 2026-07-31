# Copyright (C) 2023 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only

import shutil
import zipfile
from os.path import join
from pathlib import Path

from pythonforandroid.logger import info
from pythonforandroid.recipe import PythonRecipe


class PySideRecipe(PythonRecipe):
    version = '6.9.2'
    url = "https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.9.2-6.9.2-cp311-cp311-android_aarch64.whl"
    wheel_name = 'PySide6-6.9.2-6.9.2-cp311-cp311-android_aarch64.whl'
    depends = ["shiboken6"]
    call_hostpython_via_targetpython = False
    install_in_hostpython = False

    def build_arch(self, arch):
        """Unzip the wheel and copy into site-packages of target"""

        self.wheel_path = join(self.ctx.packages_path, self.name, self.wheel_name)
        info("Copying libc++_shared.so from SDK to be loaded on startup")
        libcpp_path = f"{self.ctx.ndk.sysroot_lib_dir}/{arch.command_prefix}/libc++_shared.so"
        shutil.copyfile(libcpp_path, Path(self.ctx.get_libs_dir(arch.arch)) / "libc++_shared.so")

        info(f"Installing {self.name} into site-packages")
        with zipfile.ZipFile(self.wheel_path, "r") as zip_ref:
            info("Unzip wheels and copy into {}".format(self.ctx.get_python_install_dir(arch.arch)))
            zip_ref.extractall(self.ctx.get_python_install_dir(arch.arch))

        install_dir = Path(self.ctx.get_python_install_dir(arch.arch))
        pyside_dir = install_dir / "PySide6"
        qt_lib_dir = pyside_dir / "Qt" / "lib"
        libs_dir = Path(self.ctx.get_libs_dir(arch.arch))

        info("Copying Qt libraries to be loaded on startup")
        shutil.copytree(qt_lib_dir, libs_dir, dirs_exist_ok=True)

        # Copy PySide6 binding libraries (.abi3.so files)
        for so_file in pyside_dir.glob("*.abi3.so"):
            shutil.copyfile(so_file, libs_dir / so_file.name)

        # Copy platform plugin if present
        plugin_path = pyside_dir / "Qt" / "plugins" / "platforms" / f"libplugins_platforms_qtforandroid_{arch.arch}.so"
        if plugin_path.exists():
            shutil.copyfile(plugin_path, libs_dir / plugin_path.name)


recipe = PySideRecipe()
