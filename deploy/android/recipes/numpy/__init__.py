from pythonforandroid.recipes.numpy import NumpyRecipe as BaseNumpyRecipe


class NumpyRecipe(BaseNumpyRecipe):
    # meson-python is required by numpy's PEP 517 build backend.
    # Build isolation is disabled globally in p4a's PyProjectRecipe so the
    # p4a-built hostpython can import the backend from hostpython site-packages.
    hostpython_prerequisites = BaseNumpyRecipe.hostpython_prerequisites + [
        "meson-python",
    ]


recipe = NumpyRecipe()
