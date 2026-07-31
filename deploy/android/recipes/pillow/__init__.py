import os

from pythonforandroid.recipe import PyProjectRecipe


class PillowRecipe(PyProjectRecipe):
    """Pillow recipe ensuring the setuptools>=77 backend is available.

    Pillow 11.3.0 uses a custom PEP 517 backend located in _custom_build/backend.py,
    which imports setuptools.build_meta. Build isolation is disabled so setuptools
    must be present in the hostpython used for building wheels.
    """

    # Use _version/_url directly so the url is available regardless of
    # whether p4a's RecipeMeta rewrote the class attributes.
    _version = "11.3.0"
    _url = "https://pypi.python.org/packages/source/p/pillow/pillow-{version}.tar.gz"
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

    def get_recipe_env(self, arch, **kwargs):
        env = super().get_recipe_env(arch, **kwargs)
        # Point Pillow to the NDK zlib and disable host pkg-config so that
        # Pillow does not pick up x86_64 libraries/headers during cross-compile.
        env["ZLIB_ROOT"] = (
            f"{arch.ndk_lib_dir_versioned}:"
            f"{self.ctx.ndk.sysroot_include_dir}"
        )
        env["PKG_CONFIG"] = "/bin/false"
        # Unset host paths that Pillow's setup.py inspects.
        for key in (
            "C_INCLUDE_PATH",
            "CPLUS_INCLUDE_PATH",
            "LIBRARY_PATH",
            "LD_RUN_PATH",
            "PKG_CONFIG_PATH",
        ):
            env.pop(key, None)
        return env

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
