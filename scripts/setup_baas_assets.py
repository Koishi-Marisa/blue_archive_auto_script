#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BAAS Android Asset Packaging Script

Packages the current BAAS Python codebase and its runtime dependencies into
app/src/main/assets/baas so that the Android Gradle build can bundle them.

Usage:
    python scripts/setup_baas_assets.py
    python scripts/setup_baas_assets.py --clean
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── Config ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "app" / "src" / "main" / "assets" / "baas"
BAAS_VERSION_FILE = PROJECT_ROOT / ".baasversion"

# Directories/files to copy from the repo root into the asset bundle
BAAS_INCLUDES = [
    "core",
    "gui",
    "module",
    "src",
    "main.py",
    "cli.example.py",
    "service.example.py",
    "requirements.txt",
]

# Paths to exclude from the copy (large/non-Android assets, build artifacts)
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
    "deploy",
    "docs",
    "develop_tools",
}


def log(msg: str):
    print(f"[setup_baas_assets] {msg}")


def should_exclude(path: Path) -> bool:
    """Return True if any path component matches an exclude pattern."""
    for part in path.parts:
        for pat in EXCLUDE_PATTERNS:
            if pat.startswith("*"):
                if part.endswith(pat.lstrip("*")):
                    return True
            elif part == pat:
                return True
    return False


def copy_baas_source():
    """Copy BAAS Python source tree into the assets directory."""
    log("Copying BAAS source files...")
    for item_name in BAAS_INCLUDES:
        src = PROJECT_ROOT / item_name
        if not src.exists():
            log(f"  Skip missing item: {item_name}")
            continue
        dst = ASSETS_DIR / item_name
        if dst.exists():
            shutil.rmtree(dst, ignore_errors=True) if dst.is_dir() else dst.unlink()
        if src.is_dir():
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*EXCLUDE_PATTERNS))
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        log(f"  Copied {item_name}")


def install_python_dependencies():
    """Install Android-compatible Python deps into the assets directory."""
    site_packages = ASSETS_DIR / "site-packages"
    site_packages.mkdir(parents=True, exist_ok=True)

    requirements = PROJECT_ROOT / "requirements.txt"
    if not requirements.exists():
        log("No requirements.txt found, skipping dependency install")
        return

    log(f"Installing Python dependencies into {site_packages}...")
    # Filter out platform-specific packages that cannot run on Android
    skip_packages = {
        "pyqt5", "pyqt-fluent-widgets", "pyautogui", "mss", "win11toast",
        "pyinstaller", "gevent",
    }
    filtered_req = []
    for line in requirements.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # Extract package name (before any version specifier or extras)
        pkg_name = stripped.split("[")[0].split("=")[0].split("<")[0].split(">")[0].strip().lower()
        if pkg_name in skip_packages:
            log(f"  Skip platform-specific package: {stripped}")
            continue
        filtered_req.append(stripped)

    if not filtered_req:
        log("No remaining requirements to install")
        return

    pip_cmd = [
        sys.executable, "-m", "pip", "install",
        "--no-deps" if os.environ.get("BAAS_PIP_NO_DEPS") else "",
        "--target", str(site_packages),
        "--no-cache-dir",
        "--upgrade",
    ]
    pip_cmd = [c for c in pip_cmd if c]
    pip_cmd.extend(filtered_req)

    subprocess.run(pip_cmd, check=True)


def write_version_file():
    """Write a version marker used by the Android build."""
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
    parser = argparse.ArgumentParser(description="Package BAAS assets for Android")
    parser.add_argument("--clean", action="store_true", help="Clean existing assets before packaging")
    parser.add_argument("--skip-deps", action="store_true", help="Skip installing Python dependencies")
    args = parser.parse_args()

    if args.clean and ASSETS_DIR.exists():
        log(f"Cleaning {ASSETS_DIR}")
        shutil.rmtree(ASSETS_DIR)

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    copy_baas_source()
    if not args.skip_deps:
        install_python_dependencies()
    write_version_file()

    log("Done.")


if __name__ == "__main__":
    main()
