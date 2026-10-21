import os
import sys
import time

from OpenGL.GL import (glReadPixels, glReadBuffer, glBindFramebuffer, glPixelStorei, glGetIntegerv,
                       GL_RGB, GL_UNSIGNED_BYTE, GL_BACK, GL_READ_FRAMEBUFFER, GL_PACK_ALIGNMENT)
from PIL import Image # pip install Pillow


def screenshot_directory():
    """
    The folder of the example that is being run (the __main__ script), so screenshots land next to it.
    Falls back to the current working directory when there is no script (interactive session, notebook).
    """
    main_file = getattr(sys.modules.get("__main__"), "__file__", None)
    if main_file:
        return os.path.dirname(os.path.abspath(main_file))
    return os.getcwd()


def _unique_path(directory, timestamp):
    """screenshot_<timestamp>.png, with a -1, -2, ... suffix if that second already has one."""
    path = os.path.join(directory, f"screenshot_{timestamp}.png")
    n = 0
    while os.path.exists(path):
        n += 1
        path = os.path.join(directory, f"screenshot_{timestamp}-{n}.png")
    return path


def save_screenshot(filename=None, width=1024, height=768, directory=None):
    """
    Reads the pixels of the window's back buffer and saves them as screenshot_<YYYYmmdd-HHMMSS>.png
    in `directory` (default: the folder of the running example, see screenshot_directory()).
    `filename` is kept for backward compatibility and is ignored: files are always named by timestamp.
    Call it after the frame is drawn and before the buffer swap. Returns the saved path, or None on failure.
    """
    directory = screenshot_directory() if directory is None else directory
    path = _unique_path(directory, time.strftime("%Y%m%d-%H%M%S"))
    try:
        # read the window's own back buffer, even if an example left an offscreen FBO bound
        glBindFramebuffer(GL_READ_FRAMEBUFFER, 0)
        glReadBuffer(GL_BACK)
        # rows are not padded to 4 bytes, otherwise widths that aren't a multiple of 4 come out skewed
        previous_alignment = glGetIntegerv(GL_PACK_ALIGNMENT)
        glPixelStorei(GL_PACK_ALIGNMENT, 1)
        gl_pixels = glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE)
        glPixelStorei(GL_PACK_ALIGNMENT, previous_alignment)
        image = Image.frombytes("RGB", (width, height), gl_pixels)
        # flip because OpenGL has the origin at the bottom-left corner
        image = image.transpose(Image.FLIP_TOP_BOTTOM)
        image.save(path)
        print(f"Screenshot saved: {path}")
        return path
    except Exception as e:
        print(f"Failed to capture screenshot: {e}")
        return None
