from pythonforandroid.recipe import PyProjectRecipe


class PillowRecipe(PyProjectRecipe):
    """Pillow recipe ensuring the setuptools>=77 backend is available.

    Pillow 11.3.0 uses a custom PEP 517 backend located in _custom_build/backend.py,
    which imports setuptools.build_meta. Build isolation is disabled so setuptools
    must be present in the hostpython used for building wheels.
    """

    version = "11.3.0"
    hostpython_prerequisites = ["setuptools>=77"]

    def build_arch(self, arch):
        # Force --no-isolation because buildozer resets p4a after our build.py
        # patch, which would otherwise leave PyProjectRecipe using isolated
        # venvs that cannot access setuptools>=77.
        self.extra_build_args = ["--no-isolation"] + list(self.extra_build_args)
        super().build_arch(arch)


recipe = PillowRecipe()
