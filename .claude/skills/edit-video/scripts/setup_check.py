#!/usr/bin/env python3
"""First-run setup for edit-video: checks Python, ffmpeg, the Python
packages and the segmentation model, and installs whatever is missing
without the buyer typing anything. Safe to run before every command that
needs it - it's a fast no-op once everything is already in place.

Never prints a raw traceback for something expected to fail (no internet,
missing ffmpeg, a blocked download). Everything expected is caught and
turned into one plain-English line.

Usage: python3 setup_check.py
Exit code 0 = ready to use. Exit code 1 = couldn't finish; last printed
line is the one thing to tell the buyer.
"""
import importlib
import os
import platform
import shutil
import subprocess
import sys
import time

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
REQS = os.path.join(SCRIPTS_DIR, "requirements.txt")
MODEL_PATH = os.path.join(SCRIPTS_DIR, "selfie_segmenter.tflite")
IMPORT_NAMES = ["mediapipe", "cv2", "PIL", "numpy"]


def check_python():
    if sys.version_info < (3, 8):
        print(f"Your Python ({platform.python_version()}) is too old for this. "
              f"Please install Python 3.9 or newer from python.org, then try again.")
        return False
    return True


def missing_modules():
    missing = []
    for mod in IMPORT_NAMES:
        try:
            importlib.import_module(mod)
        except Exception:
            missing.append(mod)
    return missing


def ensure_packages():
    if not missing_modules():
        return True
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", REQS],
                        check=True, capture_output=True, text=True, timeout=900)
    except Exception:
        pass

    still_missing = missing_modules()
    if still_missing and platform.system() == "Linux":
        # mediapipe needs these two graphics libraries on some Linux boxes
        try:
            subprocess.run(["apt-get", "install", "-y", "libegl1", "libgles2"],
                            check=True, capture_output=True, text=True, timeout=600)
        except Exception:
            pass
        still_missing = missing_modules()

    if still_missing:
        print("Couldn't set up the video tools automatically. Please check your "
              "internet connection and try again - if it keeps failing, ask for "
              "help in the course community.")
        return False
    return True


def ensure_ffmpeg():
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return True
    system = platform.system()
    try:
        if system == "Darwin" and shutil.which("brew"):
            subprocess.run(["brew", "install", "ffmpeg"], check=True,
                            capture_output=True, text=True, timeout=1200)
        elif system == "Linux" and shutil.which("apt-get"):
            subprocess.run(["apt-get", "install", "-y", "ffmpeg"], check=True,
                            capture_output=True, text=True, timeout=1200)
        elif system == "Windows" and shutil.which("winget"):
            subprocess.run(["winget", "install", "-e", "--id", "Gyan.FFmpeg"], check=True,
                            capture_output=True, text=True, timeout=1200)
    except Exception:
        pass

    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return True
    print("This computer is missing a free video tool called ffmpeg, and it couldn't "
          "be installed automatically here. Please ask whoever set up this computer "
          "to install \"ffmpeg\", then try again.")
    return False


def ensure_model(retries=3):
    if os.path.exists(MODEL_PATH) and os.path.getsize(MODEL_PATH) > 0:
        return True
    sys.path.insert(0, SCRIPTS_DIR)
    from matte import ensure_model as _ensure_model
    for attempt in range(retries):
        try:
            _ensure_model(MODEL_PATH)
            return True
        except Exception:
            if attempt < retries - 1:
                time.sleep(2 * (attempt + 1))
    print("Couldn't download a small required file - no internet, or it's being "
          "blocked. Please check your connection and try again in a moment.")
    return False


def main():
    if not check_python():
        sys.exit(1)

    need_packages = bool(missing_modules())
    need_ffmpeg = not (shutil.which("ffmpeg") and shutil.which("ffprobe"))
    need_model = not (os.path.exists(MODEL_PATH) and os.path.getsize(MODEL_PATH) > 0)

    if need_packages or need_ffmpeg or need_model:
        print("Setting things up, this takes about a minute, only once.")

    ok = True
    if need_packages:
        ok = ensure_packages() and ok
    if ok and need_ffmpeg:
        ok = ensure_ffmpeg() and ok
    if ok:
        ok = ensure_model() and ok

    if ok:
        print("READY")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
