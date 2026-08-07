"""
Shared helper for pyGLV's GUI-opening unit tests (test_Scene.py and friends): every one of those
tests runs `while running: running = self.scene.render()`, and
Elements.pyGLV.GUI.Viewer.RenderWindow.event_input_process() only ever sets `running = False` on
a real SDL_QUIT or ESC keydown pulled from the live SDL event queue -- so today, running the test
suite means a human has to sit at the keyboard and press ESC (or close the window) for every test
that opens one.

auto_quit_after() schedules a synthetic SDL_QUIT event on a background timer, delivered through
the same SDL event queue event_input_process() already reads -- so the loop exits itself exactly
as if a human had pressed ESC, with no change needed to the loop itself.
"""

import ctypes
import threading

import sdl2


def auto_quit_after(seconds=2.0):
    """
    Push a synthetic SDL_QUIT event onto the SDL event queue after `seconds`, so any
    `while running: running = scene.render()` loop exits on its own instead of needing a human to
    press ESC or close the window.

    Call this once, any time after scene.init() (which is what actually calls SDL_Init) and
    before entering the loop. Returns the underlying threading.Timer, mainly so a caller could
    timer.cancel() it if the test finishes on its own first -- normally you can just let it fire.
    """
    def _push_quit_event():
        event = sdl2.SDL_Event()
        event.type = sdl2.SDL_QUIT
        sdl2.SDL_PushEvent(ctypes.byref(event))

    timer = threading.Timer(seconds, _push_quit_event)
    timer.daemon = True
    timer.start()
    return timer
