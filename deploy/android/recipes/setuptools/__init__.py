from pythonforandroid.recipe import PythonRecipe


class SetuptoolsRecipe(PythonRecipe):
    # p4a's bundled 69.2.0 recipe uses setuptools.dist.check_test_suite, which
    # was removed in setuptools 72+. Pillow/meson-python need a modern
    # setuptools in the hostpython used for PEP 517 builds, so keep the target
    # setuptools recipe at a compatible version below 81 (where dry_run was
    # removed from distutils.util.byte_compile).
    version = '80.10.2'
    url = 'https://pypi.python.org/packages/source/s/setuptools/setuptools-{version}.tar.gz'
    call_hostpython_via_targetpython = False
    install_in_hostpython = True


recipe = SetuptoolsRecipe()
