#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import jinja2
import shutil
import typer
import subprocess
from typing import List

ARCH_MAP = {
    'arm64-v8a': {
        'wheel': 'aarch64.whl',
    },
    'x86_64': {
        'wheel': 'x86_64.whl',
    }
}

ARCH = 'arm64-v8a'
ANDROID_SDK_PATH = './.pyside6_android_deploy/android-sdk'
ANDROID_NDK_PATH = './.pyside6_android_deploy/android-ndk/android-ndk-r26b'
ICON_PATH = 'gui/assets/logo.png'
BIN_DIR = './bin'
MIN_API = 24
BUILD_DIR = 'build'
JARS_PATH = [
    'deploy/android/jar/PySide6/jar/Qt6Android.jar',
    'deploy/android/jar/PySide6/jar/Qt6AndroidBindings.jar'
]
PYSIDE6_WHEEL_BASIC_URL = 'https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.9.2-6.9.2-cp311-cp311-android_'
SHIBOKEN6_WHEEL_BASIC_URL = 'https://download.qt.io/official_releases/QtForPython/shiboken6/shiboken6-6.9.0-6.9.0-cp311-cp311-android_'
GRADLE_WRAPPER_TEMPLATE = '.buildozer/android/platform/build-{arch}/dists/boa/gradlew'

def cwd_path(path: str):
    return os.path.abspath(os.path.join(os.getcwd(), path))

def self_path(path: str):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), path))

def proj_path(path: str):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', path))

def build_path(path: str):
    return os.path.abspath(os.path.join(proj_path(BUILD_DIR), path))

def log(msg: str):
    print(f'[{os.path.basename(__file__)}] {msg}', flush=True)

def render(src: str, dst: str, ctx: dict):
    """Copy and/or render a file to a destination file."""
    if os.path.isfile(src):
        # Ensure destination directory exists
        dst_dir = os.path.dirname(dst)
        if dst_dir and not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        if '.templ.' in src:
            log(f'Rendering {src} to {dst}')
            with open(src, 'r') as f:
                template = jinja2.Template(f.read())
            with open(dst, 'w') as f:
                f.write(template.render(ctx))
        else:
            log(f'Copying {src} to {dst}')
            shutil.copy(src, dst)
    elif os.path.isdir(src):
        if not os.path.exists(dst):
            os.makedirs(dst)
        for root, dirs, files in os.walk(src):
            # Compute destination relative to the source directory to avoid absolute path join issues
            rel_root = os.path.relpath(root, src)
            for file in files:
                src_file = os.path.join(root, file)
                dst_root = dst if rel_root == '.' else os.path.join(dst, rel_root)
                dst_file = os.path.join(dst_root, file)
                if '.templ.' in dst_file:
                    dst_file = dst_file.replace('.templ', '')
                render(src_file, dst_file, ctx)
    else:
        raise FileNotFoundError(f'{src} not found')


def _configure():
    if ARCH not in ARCH_MAP:
        raise typer.BadParameter(f'Unsupported arch: {ARCH}')
    arch_cfg = ARCH_MAP[ARCH]
    log('Reading requirements...')
    with open(self_path('requirements.txt'), 'r') as f:
        requirements = f.read()
    requirements = [line.strip() for line in requirements.splitlines() if line.strip()]
    log(f'Requirements: {requirements}')

    log('Generating buildozer.spec...')
    render(self_path('buildozer.templ.spec'), proj_path('buildozer.spec'), {
        'android_ndk_path': proj_path(ANDROID_NDK_PATH),
        'android_sdk_path': proj_path(ANDROID_SDK_PATH),
        'local_recipes_path': build_path('recipes'),
        'requirements': ', '.join(requirements),
        'icon_path': proj_path(ICON_PATH),
        'bin_dir': proj_path(BIN_DIR),
        'min_api': MIN_API,
        'jars_path': ', '.join([proj_path(path) for path in JARS_PATH]),
        'p4a_hook_path': self_path('p4a_hook.py'),
        'arch': ARCH
    })

    # Ensure build directory exists before downloading wheels and generating recipes
    os.makedirs(build_path(''), exist_ok=True)
    ensure_pyside6_shiboken6(arch_cfg)

def ensure_pyside6_shiboken6(arch):
    log('Check and download PySide6 wheels...')
    wheel_tag = arch['wheel']

    # download resource
    pyside6_path = build_path(f'PySide6-6.9.2-6.9.2-cp311-cp311-android_{wheel_tag}')
    pyside6_url = PYSIDE6_WHEEL_BASIC_URL + wheel_tag
    download_artifact(pyside6_path, pyside6_url)

    shiboken6_path = build_path(f'shiboken6-6.9.0-6.9.0-cp311-cp311-android_{wheel_tag}')
    shiboken6_url = SHIBOKEN6_WHEEL_BASIC_URL + wheel_tag
    download_artifact(shiboken6_path, shiboken6_url)

    log('Extracting Qt jars from PySide6 wheel...')
    extract_jars_from_wheel(pyside6_path)

    log('Generating recipes...')
    if os.path.exists(build_path('recipes')):
        log(f'Removing existing recipes...')
        shutil.rmtree(build_path('recipes'))
    render(self_path('recipes'), build_path('recipes'), {
        'pyside6_wheel_path': pyside6_path,
        'shiboken6_wheel_path': shiboken6_path
    })

def download_artifact(path: str, url: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        log(f'Downloading artifact from to {path}...')
        os.system(f'curl -L {url} -o {path}')

def extract_jars_from_wheel(wheel_path: str):
    """Extract Android Qt jars required by buildozer from the PySide6 wheel."""
    import zipfile
    jar_names = ['Qt6Android.jar', 'Qt6AndroidBindings.jar']
    jar_prefix = 'PySide6/jar/'
    for jar_name in jar_names:
        jar_dest = proj_path(f'deploy/android/jar/PySide6/jar/{jar_name}')
        if os.path.exists(jar_dest):
            continue
        os.makedirs(os.path.dirname(jar_dest), exist_ok=True)
        with zipfile.ZipFile(wheel_path, 'r') as zf:
            source = f'{jar_prefix}{jar_name}'
            if source not in zf.namelist():
                raise FileNotFoundError(f'Required jar {source} not found in {wheel_path}')
            log(f'Extracting {source} to {jar_dest}')
            with zf.open(source) as src, open(jar_dest, 'wb') as dst:
                dst.write(src.read())

P4A_URL = 'https://github.com/XcantloadX/python-for-android.git'
P4A_BRANCH = 'develop'
P4A_COMMIT = '4838a0a2455783ad511478e44bc661ad5153bb42'
P4A_DIR = '.buildozer/android/platform/python-for-android'


def _prepare_p4a():
    """Ensure python-for-android is cloned and patched for CI build."""
    p4a_path = proj_path(P4A_DIR)
    if not os.path.exists(p4a_path):
        log('Cloning python-for-android...')
        os.makedirs(os.path.dirname(p4a_path), exist_ok=True)
        subprocess.run([
            'git', 'clone', '--branch', P4A_BRANCH, P4A_URL, p4a_path
        ], check=True)
        subprocess.run(
            ['git', 'reset', '--hard', P4A_COMMIT],
            cwd=p4a_path, check=True
        )

    recipe_py = os.path.join(p4a_path, 'pythonforandroid', 'recipe.py')
    if os.path.exists(recipe_py):
        with open(recipe_py, 'r') as f:
            content = f.read()
        # Disable PEP 517 build isolation: the p4a-built hostpython cannot
        # create working isolated venvs, so backends must be importable from
        # the hostpython site-packages prepared by install_hostpython_prerequisites.
        marker = '            "--config-setting",\n            "builddir={}".format(sub_build_dir),\n        ] + self.extra_build_args'
        replacement = '            "--config-setting",\n            "builddir={}".format(sub_build_dir),\n            "--no-isolation",\n        ] + self.extra_build_args'
        if marker in content and replacement not in content:
            log('Patching p4a PyProjectRecipe to use --no-isolation...')
            content = content.replace(marker, replacement)
            with open(recipe_py, 'w') as f:
                f.write(content)


def _build():
    os.environ['ANDROIDSDK'] = proj_path(ANDROID_SDK_PATH)
    os.environ['ANDROIDNDK'] = proj_path(ANDROID_NDK_PATH)
    _prepare_p4a()

    # Verify local recipes were generated before buildozer starts.
    local_recipes = build_path('recipes')
    for recipe_name in ('pillow', 'numpy'):
        recipe_init = os.path.join(local_recipes, recipe_name, '__init__.py')
        if not os.path.isfile(recipe_init):
            raise FileNotFoundError(f'Local recipe missing: {recipe_init}')
        with open(recipe_init, 'r') as f:
            content = f.read()
        if recipe_name == 'pillow' and '_url' not in content:
            raise ValueError(f'Pillow recipe does not define _url: {recipe_init}')
        log(f'Verified local recipe: {recipe_name}')

    result = subprocess.run(['buildozer', 'android', 'debug'])
    if result.returncode != 0:
        raise SystemExit(result.returncode)

app = typer.Typer(help="Build helper for Android deployment")

@app.command()
def build():
    """Run the build step (calls buildozer)."""
    _build()

@app.command()
def gradle(args: List[str] = typer.Argument(None, help="Arguments passed to gradlew")):
    """Run the Gradle wrapper for the Android distribution.

    Any arguments after the command are passed directly to the `gradlew` wrapper.
    If no arguments are provided, `build` is used.
    Examples:
      python deploy/android/build.py gradle clean build
      python deploy/android/build.py gradle assembleRelease
    """
    gradle_path = proj_path(GRADLE_WRAPPER_TEMPLATE.format(arch=ARCH))
    if not os.path.exists(gradle_path):
        raise FileNotFoundError(f'Gradle wrapper not found: {gradle_path}')
    # Ensure it's executable
    try:
        st = os.stat(gradle_path).st_mode
        os.chmod(gradle_path, st | 0o111)
    except Exception:
        pass
    # Build command: default to 'build' when no args provided
    cmd = [gradle_path] + (list(args) if args else ['build'])
    log(f'Running gradle wrapper: {" ".join(cmd)}')
    cwd = os.path.dirname(gradle_path) or proj_path('.')
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        raise SystemExit(result.returncode)

    # copy output if exists
    output = f'.buildozer/android/platform/build-{ARCH}/dists/boa/build/outputs/apk/debug/boa-debug.apk'
    if os.path.exists(output):
        dst = proj_path('./boa-debug.apk')
        log(f'Copying APK to {dst}')
        shutil.copy(output, dst)

@app.command("all")
def all_cmd(
    arch: str = typer.Option(ARCH, help="Android architecture (arm64-v8a, armeabi-v7a, x86_64)"),
    android_sdk_path: str = typer.Option(ANDROID_SDK_PATH, help="Android SDK path"),
    android_ndk_path: str = typer.Option(ANDROID_NDK_PATH, help="Android NDK path"),
    bin_dir: str = typer.Option(BIN_DIR, help="Output apk directory"),
    min_api: int = typer.Option(MIN_API, help="Minimum Android API level"),
):
    """Run configure then build."""
    global ANDROID_SDK_PATH, ANDROID_NDK_PATH, ARCH, BIN_DIR, MIN_API
    ARCH = arch
    ANDROID_SDK_PATH = android_sdk_path
    ANDROID_NDK_PATH = android_ndk_path
    BIN_DIR = bin_dir
    MIN_API = min_api
    _configure()
    build()

if __name__ == '__main__':
    app()
