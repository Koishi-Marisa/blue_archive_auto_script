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

    def build_arch(self, arch):
        # Force --no-isolation because buildozer resets p4a after our build.py
        # patch, which would otherwise leave PyProjectRecipe using isolated
        # venvs that cannot import setuptools.build_meta.
        self.extra_build_args = ["--no-isolation"] + list(self.extra_build_args)
        super().build_arch(arch)


recipe = PyjniusRecipe()
