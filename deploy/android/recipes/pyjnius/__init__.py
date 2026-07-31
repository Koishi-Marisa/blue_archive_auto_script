import os
import shutil
import subprocess

from pythonforandroid.logger import info
from pythonforandroid.recipes.pyjnius import PyjniusRecipe as BasePyjniusRecipe
from pythonforandroid.toolchain import shprint
import sh


class PyjniusRecipe(BasePyjniusRecipe):
    # Pyjnius is built with `python -m build` (PEP 517). The p4a-built
    # hostpython ships with an old setuptools that cannot provide
    # setuptools.build_meta in an isolated venv, so disable isolation and
    # depend on a modern setuptools recipe that is installed into hostpython.
    depends = BasePyjniusRecipe.depends + ['setuptools']
    # Pin Cython to the exact minor line pyjnius declares in pyproject.toml
    # (Cython~=3.1.2). Other recipes may leave newer/older Cython dist-info
    # directories in the shared hostpython site-packages, which confuse
    # importlib.metadata and cause the PEP 517 build-system check to fail.
    hostpython_prerequisites = [
        "Cython~=3.1.2",
        "setuptools==80.10.2",
    ]

    def _cleanup_hostpython_cython(self):
        """Remove all Cython packages and distribution metadata from hostpython.

        The shared hostpython environment accumulates Cython versions installed
        by multiple recipes (e.g. the cython target recipe installs 0.29.36,
        numpy installs 3.2.9). Leftover dist-info directories make
        `importlib.metadata.version('Cython')` return the wrong version and
        break pyjnius's `Cython~=3.1.2` requirement check.
        """
        site_dir = self.hostpython_site_dir
        if not os.path.isdir(site_dir):
            return
        removed = []
        for name in os.listdir(site_dir):
            lower = name.lower()
            path = os.path.join(site_dir, name)
            if lower in ('cython', 'cython.py'):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                removed.append(name)
            elif lower.startswith('cython-') and (
                lower.endswith('.dist-info') or '.egg-info' in lower
            ):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                removed.append(name)
        if removed:
            info(f'PYJNIUS: cleaned up conflicting Cython installations: {removed}')

    def _install_cython_cleanly(self):
        """Force a single Cython~=3.1.2 installation in hostpython."""
        self._cleanup_hostpython_cython()
        pip_options = [
            "install",
            "Cython~=3.1.2",
            "--target", self.hostpython_site_dir,
            "--python-version", self.ctx.python_recipe.version,
            "--only-binary=:all:",
            "--force-reinstall",
            "--no-deps",
        ]
        shprint(sh.pip, *pip_options)
        out = subprocess.check_output(
            [self.real_hostpython_location, '-c',
             'import importlib.metadata; print("Cython version:", '
             'importlib.metadata.version("Cython")); import Cython; '
             'print("Cython package:", Cython.__file__)'],
            text=True
        )
        info(f'PYJNIUS: Cython verification:\n{out}')

    def get_recipe_env(self, arch, **kwargs):
        env = super().get_recipe_env(arch, **kwargs)
        # PyProjectRecipe copies the hostpython binary to the target python
        # location; the copy no longer finds hostpython site-packages on its
        # own. With --no-isolation we must ensure build deps (Cython,
        # setuptools) installed into hostpython are importable.
        hostpython_site = os.path.join(
            os.path.dirname(os.path.dirname(self.real_hostpython_location)),
            'Lib', 'site-packages'
        )
        env['PYTHONPATH'] = (
            hostpython_site + os.pathsep + env.get('PYTHONPATH', '')
        ).rstrip(os.pathsep)
        return env

    def build_arch(self, arch):
        # Ensure only Cython~=3.1.2 is visible before the PEP 517 build runs.
        self._install_cython_cleanly()
        # Force --no-isolation because buildozer resets p4a after our build.py
        # patch, which would otherwise leave PyProjectRecipe using isolated
        # venvs that cannot import setuptools.build_meta.
        self.extra_build_args = ["--no-isolation"] + list(self.extra_build_args)
        super().build_arch(arch)


recipe = PyjniusRecipe()
