# Copyright (C) 2023 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only

import shutil
import zipfile
from os.path import join
from pathlib import Path

from pythonforandroid.logger import info
from pythonforandroid.recipe import PythonRecipe


class ShibokenRecipe(PythonRecipe):
    version = '6.9.0'
    url = "https://download.qt.io/official_releases/QtForPython/shiboken6/shiboken6-6.9.0-6.9.0-cp311-cp311-android_aarch64.whl"
    wheel_name = 'shiboken6-6.9.0-6.9.0-cp311-cp311-android_aarch64.whl'

    call_hostpython_via_targetpython = False
    install_in_hostpython = False

    def build_arch(self, arch):
        ''' Unzip the wheel and copy into site-packages of target'''

        self.wheel_path = join(self.ctx.packages_path, self.name, self.wheel_name)
        info('Installing {} into site-packages'.format(self.name))
        with zipfile.ZipFile(self.wheel_path, 'r') as zip_ref:
            info('Unzip wheels and copy into {}'.format(self.ctx.get_python_install_dir(arch.arch)))
            zip_ref.extractall(self.ctx.get_python_install_dir(arch.arch))

        install_dir = Path(self.ctx.get_python_install_dir(arch.arch))
        lib_dir = install_dir / "shiboken6"
        libs_dir = Path(self.ctx.get_libs_dir(arch.arch))
        shutil.copyfile(lib_dir / "libshiboken6.abi3.so",
                        libs_dir / "libshiboken6.abi3.so")


recipe = ShibokenRecipe()
