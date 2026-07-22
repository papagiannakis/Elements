from OpenGL.GL import glReadPixels, GL_RGB, GL_UNSIGNED_BYTE
from PIL import Image # pip install Pillow
import time


def save_screenshot(filename="screenshot.png", width=1024, height=768):
    """
    diavazei ta pixels apo OpenGL buffer kai ta swzei san image
    """
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"screenshot_{timestamp}.png"
    try:
        gl_pixels = glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE)
        image = Image.frombytes("RGB", (width, height), gl_pixels)
        # flip giati OpenGL exei to kentro katw aristera
        image = image.transpose(Image.FLIP_TOP_BOTTOM)
        image.save(filename)
        print(f"To screnshot exei apothikeutei ws: {filename}")
    except Exception as e:
        print(f"Den travixtike to screenshot: {e}")

