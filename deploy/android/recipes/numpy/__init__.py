from pythonforandroid.recipes.numpy import NumpyRecipe as BaseNumpyRecipe


class NumpyRecipe(BaseNumpyRecipe):
    # meson-python is required by numpy's PEP 517 build backend.
    # Build isolation is disabled so the p4a-built hostpython can import
    # the backend from the hostpython site-packages prepared by p4a.
    hostpython_prerequisites = BaseNumpyRecipe.hostpython_prerequisites + [
        "meson-python",
    ]
    extra_build_args = BaseNumpyRecipe.extra_build_args + ["--no-isolation"]


recipe = NumpyRecipe()
