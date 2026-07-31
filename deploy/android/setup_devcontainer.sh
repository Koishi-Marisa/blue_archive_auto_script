#!/bin/bash

set -e
set -u
set -o pipefail

# Base directory for all Android build dependencies
export PYSIDE6_ANDROID_DEPLOY="$(pwd)/.pyside6_android_deploy"
mkdir -p "${PYSIDE6_ANDROID_DEPLOY}"

########## Download SDK ##########
ANDROID_SDK_DIR="${PYSIDE6_ANDROID_DEPLOY}/android-sdk"
CMDLINE_TOOLS_DIR="${ANDROID_SDK_DIR}/cmdline-tools"

if [ -d "${CMDLINE_TOOLS_DIR}/latest/bin" ]; then
    echo "Android SDK already installed."
else
    echo "Downloading Android SDK command line tools..."
    mkdir -p "${ANDROID_SDK_DIR}"
    cd "${ANDROID_SDK_DIR}"
    wget -q https://dl.google.com/android/repository/commandlinetools-linux-13114758_latest.zip
    unzip -q commandlinetools-linux-13114758_latest.zip
    # Move tools into the expected cmdline-tools/latest/ location
    mkdir -p cmdline-tools/latest
    mv cmdline-tools/bin cmdline-tools/latest/
    mv cmdline-tools/lib cmdline-tools/latest/
    rm -rf cmdline-tools/NOTICE.txt cmdline-tools/source.properties 2>/dev/null || true
    rm commandlinetools-linux-13114758_latest.zip
    cd -
    # accept sdk license
    yes | "${CMDLINE_TOOLS_DIR}/latest/bin/sdkmanager" --licenses || true
fi

# Install required SDK platforms and build tools
yes | "${CMDLINE_TOOLS_DIR}/latest/bin/sdkmanager" "platforms;android-24" "build-tools;24.0.3" || true

# Create legacy tools/ path expected by buildozer/python-for-android.
# sdkmanager's launcher script resolves ../lib relative to its own location,
# so both bin and lib must be reachable from tools/.
mkdir -p "${ANDROID_SDK_DIR}/tools"
if [ ! -e "${ANDROID_SDK_DIR}/tools/bin" ]; then
    ln -sfn "${CMDLINE_TOOLS_DIR}/latest/bin" "${ANDROID_SDK_DIR}/tools/bin"
fi
if [ ! -e "${ANDROID_SDK_DIR}/tools/lib" ]; then
    ln -sfn "${CMDLINE_TOOLS_DIR}/latest/lib" "${ANDROID_SDK_DIR}/tools/lib"
fi

########## Download NDK ##########
ANDROID_NDK_VERSION="r26b"
ANDROID_NDK_DIR="${PYSIDE6_ANDROID_DEPLOY}/android-ndk/android-ndk-${ANDROID_NDK_VERSION}"

if [ -d "${ANDROID_NDK_DIR}" ]; then
    echo "Android NDK already installed."
else
    echo "Downloading Android NDK ${ANDROID_NDK_VERSION}..."
    mkdir -p "${PYSIDE6_ANDROID_DEPLOY}/android-ndk"
    cd "${PYSIDE6_ANDROID_DEPLOY}/android-ndk"
    wget -q "https://dl.google.com/android/repository/android-ndk-${ANDROID_NDK_VERSION}-linux.zip"
    unzip -q "android-ndk-${ANDROID_NDK_VERSION}-linux.zip"
    rm "android-ndk-${ANDROID_NDK_VERSION}-linux.zip"
    cd -
fi

########## Setup PATH ##########
export ANDROIDSDK="${ANDROID_SDK_DIR}"
export ANDROIDNDK="${ANDROID_NDK_DIR}"
# Link cache directory to workspace to avoid re-downloading
ln -sfn "${PYSIDE6_ANDROID_DEPLOY}" ~/.pyside6_android_deploy

########## Create Python virtual environment ##########

echo "Creating Python virtual environment..."
python -m venv .venv
echo "Activating virtual environment..."
. .venv/bin/activate
echo "Upgrading pip..."
python -m pip install --upgrade pip

echo "Installing build requirements..."
if [ -f deploy/android/requirements-build.txt ]; then
    pip install -r deploy/android/requirements-build.txt
else
    echo "deploy/android/requirements-build.txt not found, skipping build dependency installation."
fi

########## Setup pyside6-android-deploy wheels ##########
# check pyside wheels
cd .pyside6_android_deploy
if [ ! -f pyside6-*.whl ] && [ ! -f PySide6-*.whl ]; then
    echo "PySide6 wheels not found, downloading..."
    wget -q https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.9.2-6.9.2-cp311-cp311-android_aarch64.whl
fi
if [ ! -f shiboken6-*.whl ]; then
    echo "shiboken6 wheels not found, downloading..."
    wget -q https://download.qt.io/official_releases/QtForPython/shiboken6/shiboken6-6.9.0-6.9.0-cp311-cp311-android_aarch64.whl
fi
cd ..

echo "Environment setup complete."

########## Setup ADB ##########
# Prioritize IPv4 over IPv6 for ADB connection
if [ -f /etc/gai.conf ]; then
    sed -i 's/#precedence ::ffff:0:0\/96  100/precedence ::ffff:0:0\/96  100/' /etc/gai.conf || true
fi
