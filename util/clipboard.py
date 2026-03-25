"""Clipboard helper utilities for Linux desktop environments."""

from __future__ import annotations

import shutil
import subprocess


def copy_text_to_clipboard(text: str) -> bool:
    """Copy text to clipboard using available Linux clipboard tools.

    Order:
    - wl-copy (Wayland)
    - xclip (X11)
    - xsel (X11)
    """

    if shutil.which("wl-copy"):
        proc = subprocess.run(["wl-copy"], input=text.encode("utf-8"), check=False)
        return proc.returncode == 0

    if shutil.which("xclip"):
        proc = subprocess.run(
            ["xclip", "-selection", "clipboard"],
            input=text.encode("utf-8"),
            check=False,
        )
        return proc.returncode == 0

    if shutil.which("xsel"):
        proc = subprocess.run(
            ["xsel", "--clipboard", "--input"],
            input=text.encode("utf-8"),
            check=False,
        )
        return proc.returncode == 0

    return False
