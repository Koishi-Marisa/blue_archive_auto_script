from pythonforandroid.recipes.numpy import NumpyRecipe as BaseNumpyRecipe


class NumpyRecipe(BaseNumpyRecipe):
    # meson-python is required by numpy's PEP 517 build backend.
    # Build isolation is disabled so the p4a-built hostpython can import the
    # backend from hostpython site-packages prepared below.
    # Pin Cython to the same minor line pyjnius needs so the shared hostpython
    # site-packages does not end up with multiple conflicting Cython versions.
    hostpython_prerequisites = [
        "Cython~=3.1.2",
        "numpy",
        "meson-python",
    ]

    def build_arch(self, arch):
        # Force --no-isolation because buildozer resets p4a after our build.py
        # patch, which would otherwise leave PyProjectRecipe using isolated
        # venvs that cannot access meson-python.
        self.extra_build_args = ["--no-isolation"] + list(self.extra_build_args)
        super().build_arch(arch)


recipe = NumpyRecipe()
