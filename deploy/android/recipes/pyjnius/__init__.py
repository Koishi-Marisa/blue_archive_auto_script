import os

from pythonforandroid.recipes.pyjnius import PyjniusRecipe as BasePyjniusRecipe


class PyjniusRecipe(BasePyjniusRecipe):
    # Pyjnius is built with `python -m build` (PEP 517). The p4a-built
    # hostpython ships with an old setuptools that cannot provide
    # setuptools.build_meta in an isolated venv, so disable isolation and
    # depend on a modern setuptools recipe that is installed into hostpython.
    depends = BasePyjniusRecipe.depends + ['setuptools']
    hostpython_prerequisites = BasePyjniusRecipe.hostpython_prerequisites + [
        "setuptools==80.10.2",
    ]

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
        # Force --no-isolation because buildozer resets p4a after our build.py
        # patch, which would otherwise leave PyProjectRecipe using isolated
        # venvs that cannot import setuptools.build_meta.
        self.extra_build_args = ["--no-isolation"] + list(self.extra_build_args)
        # Debug: verify Cython is visible from the copied python before build.
        hostpython_site = self.hostpython_site_dir
        python_exe = self.ctx.python_recipe.python_exe
        from pythonforandroid.logger import info
        info(f'PYJNIUS DEBUG: hostpython_site_dir={hostpython_site}')
        info(f'PYJNIUS DEBUG: python_exe={python_exe}')
        info(f'PYJNIUS DEBUG: PYTHONPATH will be {self.get_recipe_env(arch, with_flags_in_cc=True).get("PYTHONPATH", "")}')
        import subprocess
        try:
            out = subprocess.check_output(
                [python_exe, '-c',
                 'import sys; print(sys.path); import importlib.util; '
                 'print("cython spec:", importlib.util.find_spec("Cython"))'],
                env=self.get_recipe_env(arch, with_flags_in_cc=True),
                stderr=subprocess.STDOUT, text=True
            )
            info(f'PYJNIUS DEBUG: import check output:\n{out}')
        except Exception as e:
            info(f'PYJNIUS DEBUG: import check failed: {e}')
        try:
            info(f'PYJNIUS DEBUG: listing {hostpython_site}: {os.listdir(hostpython_site)}')
        except Exception as e:
            info(f'PYJNIUS DEBUG: listing failed: {e}')
        super().build_arch(arch)


recipe = PyjniusRecipe()
