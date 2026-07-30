#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BAAS Android Chaquopy asset preparation script.

Copies BAAS Python source code into app/src/main/python so Chaquopy can bundle
it into the APK. Also writes a .baasversion marker.

Usage:
    python scripts/prepare_chaquopy_assets.py
    python scripts/prepare_chaquopy_assets.py --clean
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON_ROOT = PROJECT_ROOT / "app" / "src" / "main" / "python"
BAAS_VERSION_FILE = PROJECT_ROOT / ".baasversion"

# Top-level Python packages/files to include in the APK.
BAAS_INCLUDES = [
    "core",
    "module",
    "src",
    "config",
    "main.py",
    "main_android.py",
    "requirements-android.txt",
]

EXCLUDE_PATTERNS = {
    "__pycache__",
    ".git",
    ".github",
    ".idea",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*.so",
    "*.dylib",
    "*.dll",
    "*.exe",
    "build",
    "dist",
}


def log(msg: str):
    print(f"[prepare_chaquopy_assets] {msg}")


def should_exclude(path: Path) -> bool:
    for part in path.parts:
        for pat in EXCLUDE_PATTERNS:
            if pat.startswith("*"):
                if part.endswith(pat.lstrip("*")):
                    return True
            elif part == pat:
                return True
    return False


def copy_baas_sources():
    log(f"Copying BAAS sources to {PYTHON_ROOT}")
    PYTHON_ROOT.mkdir(parents=True, exist_ok=True)

    for item_name in BAAS_INCLUDES:
        src = PROJECT_ROOT / item_name
        if not src.exists():
            log(f"  Skip missing item: {item_name}")
            continue
        dst = PYTHON_ROOT / item_name
        if dst.exists():
            if dst.is_dir():
                shutil.rmtree(dst)
            else:
                dst.unlink()
        if src.is_dir():
            shutil.copytree(src, dst, ignore=lambda src, names: [n for n in names if should_exclude(Path(src) / n)])
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        log(f"  Copied {item_name}")


def write_version_file():
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--always"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        version = result.stdout.strip()
    except Exception:
        version = "unknown"
    BAAS_VERSION_FILE.write_text(version + "\n", encoding="utf-8")
    log(f"Wrote BAAS version: {version}")


def main():
    parser = argparse.ArgumentParser(description="Prepare BAAS Chaquopy assets")
    parser.add_argument("--clean", action="store_true", help="Clean app/src/main/python before copying")
    args = parser.parse_args()

    if args.clean and PYTHON_ROOT.exists():
        log(f"Cleaning {PYTHON_ROOT}")
        shutil.rmtree(PYTHON_ROOT)

    copy_baas_sources()
    write_version_file()
    log("Done.")


if __name__ == "__main__":
    main()
