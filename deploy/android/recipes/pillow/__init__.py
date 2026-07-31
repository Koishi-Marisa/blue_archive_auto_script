from pythonforandroid.recipe import PyProjectRecipe


class PillowRecipe(PyProjectRecipe):
    """Pillow recipe ensuring the setuptools>=77 backend is available.

    Pillow 11.3.0 uses a custom PEP 517 backend located in _custom_build/backend.py,
    which imports setuptools.build_meta. Build isolation is disabled so setuptools
    must be present in the hostpython used for building wheels.
    """

    version = "11.3.0"
    url = "https://pypi.python.org/packages/source/p/pillow/pillow-{version}.tar.gz"
    hostpython_prerequisites = ["setuptools>=77"]

    # Optional image libraries are disabled for Android cross-compilation.
    # Only zlib is kept because Pillow requires it and the Android NDK
    # sysroot provides zlib headers/libraries.
    _pillow_features = [
        "platform-guessing=disable",
        "jpeg=disable",
        "jpeg2000=disable",
        "freetype=disable",
        "tiff=disable",
        "webp=disable",
        "imagequant=disable",
        "lcms=disable",
        "xcb=disable",
        "raqm=disable",
        "fribidi=disable",
        "harfbuzz=disable",
        "avif=disable",
    ]

    def build_arch(self, arch):
        # Force --no-isolation because buildozer resets p4a after our build.py
        # patch, which would otherwise leave PyProjectRecipe using isolated
        # venvs that cannot access setuptools>=77.
        args = ["--no-isolation"]
        for cfg in self._pillow_features:
            args.extend(["--config-setting", cfg])
        self.extra_build_args = args + list(self.extra_build_args)
        super().build_arch(arch)


recipe = PillowRecipe()
