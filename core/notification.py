import os
import sys

# Check if the current OS is Windows
try:
    from win11toast import notify as _notify
    from win11toast import toast as _toast
except ImportError:
    _notify = None
    _toast = None

app_id = 'BlueArchiveAutoScript.exe'
icon_path = '/gui/assets/logo.png'

# python-for-android / Chaquopy environment detection.
_IS_ANDROID = sys.platform == 'android' or os.environ.get('P4A_BOOTSTRAP') is not None


def get_root_path():
    root_path = os.path.abspath(os.path.dirname(__file__))
    while True:
        if "window.py" in os.listdir(root_path):
            return root_path
        parent = os.path.dirname(root_path)
        if parent == root_path:
            raise FileNotFoundError("Could not find project root containing window.py")
        root_path = parent


def notify(title=None, body=None):
    if _IS_ANDROID:
        print(f"[notify] {title}: {body}")
        return

    root_path = get_root_path()
    if _notify is None:
        print(f"{title}: {body}")
        return

    _notify(
        title=title,
        body=body,
        app_id='BlueArchiveAutoScript.exe',
        icon=root_path + icon_path,
    )


def toast(title=None, body=None, button=None, duration=None):
    if _IS_ANDROID:
        print(f"[toast] {title}: {body}")
        return None

    root_path = get_root_path()
    if _toast is None:
        print(f"{title}: {body}")
        return None

    return _toast(
        title=title,
        body=body,
        app_id='BlueArchiveAutoScript.exe',
        icon=root_path + icon_path,
        button=button,
        duration=duration
    )
