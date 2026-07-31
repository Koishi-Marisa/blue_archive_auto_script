from pythonforandroid.recipe import PyProjectRecipe


class PillowRecipe(PyProjectRecipe):
    """Pillow recipe ensuring the setuptools>=77 backend is available.

    Pillow 11.3.0 uses a custom PEP 517 backend located in _custom_build/backend.py,
    which imports setuptools.build_meta. Build isolation is disabled globally in
    p4a's PyProjectRecipe, so setuptools must be present in the hostpython used
    for building wheels.
    """

    version = "11.3.0"
    hostpython_prerequisites = ["setuptools>=77"]


recipe = PillowRecipe()
