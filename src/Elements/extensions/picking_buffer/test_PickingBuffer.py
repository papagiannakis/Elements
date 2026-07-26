import numpy as np
import sdl2
import OpenGL.GL as gl

from PickingBuffer import PickingSystem


# -------------------------
# helpers
# -------------------------

def ok(name):
    print(f"{name} : SUCCESS")

def fail(name, reason):
    print(f"{name} : FAILED -> {reason}")

def expect(name, cond, reason="condition false"):
    if cond:
        ok(name)
    else:
        fail(name, reason)


# -------------------------
# mock OpenGL
# -------------------------

def mock_gl_success():
    gl.glGenFramebuffers = lambda n: 1
    gl.glGenTextures = lambda n: 2
    gl.glGenRenderbuffers = lambda n: 3
    gl.glBindFramebuffer = lambda *a: None
    gl.glBindTexture = lambda *a: None
    gl.glBindRenderbuffer = lambda *a: None
    gl.glFramebufferTexture2D = lambda *a: None
    gl.glFramebufferRenderbuffer = lambda *a: None
    gl.glRenderbufferStorage = lambda *a: None
    gl.glTexImage2D = lambda *a: None
    gl.glTexParameteri = lambda *a: None
    gl.glViewport = lambda *a: None
    gl.glClearColor = lambda *a: None
    gl.glClear = lambda *a: None
    gl.glDisable = lambda *a: None
    gl.glEnable = lambda *a: None
    gl.glCheckFramebufferStatus = lambda x: gl.GL_FRAMEBUFFER_COMPLETE
    gl.glReadPixels = lambda x, y, w, h, f, t: bytes([1, 0, 0])


# -------------------------
# mock SDL mouse
# -------------------------

_mouse_sequence = []

def mock_mouse_sequence(seq):
    global _mouse_sequence
    _mouse_sequence = seq.copy()

def mock_get_mouse_state(x, y):
    if not _mouse_sequence:
        return 0
    state, px, py = _mouse_sequence.pop(0)
    x.value = px
    y.value = py
    return state


# -------------------------
# TESTS
# -------------------------

def test_init_fbo():
    name = "test_init_fbo"
    try:
        mock_gl_success()
        ps = PickingSystem(100, 100)
        ps.init()
        expect(name, ps.fbo is not None and ps.tex_color is not None and ps.rbo_depth is not None)
    except Exception as e:
        fail(name, str(e))


def test_resize_updates_dimensions():
    name = "test_resize_updates_dimensions"
    try:
        mock_gl_success()
        ps = PickingSystem(100, 100)
        ps.init()
        ps.resize(200, 150)
        expect(name, ps.width == 200 and ps.height == 150)
    except Exception as e:
        fail(name, str(e))


def test_camera_matrix_set():
    name = "test_camera_matrix_set"
    ps = PickingSystem(10, 10)
    P = np.eye(4) * 2
    V = np.eye(4) * 3
    ps.set_camera_matrices(P, V)
    expect(name, np.all(ps.projMat == P) and np.all(ps.view == V))


def test_begin_resets_ids():
    name = "test_begin_resets_ids"
    mock_gl_success()
    ps = PickingSystem(10, 10)
    ps.init()
    ps.entity_to_id = {"a": 1}
    ps.id_to_entity = {1: "a"}
    ps._next_id = 99
    ps.begin_picking_pass()
    expect(name, ps._next_id == 1 and not ps.entity_to_id and not ps.id_to_entity)


def test_pick_zero_returns_none():
    name = "test_pick_zero_returns_none"
    mock_gl_success()
    gl.glReadPixels = lambda *a: bytes([0, 0, 0])
    ps = PickingSystem(10, 10)
    ps.init()
    ent, pid = ps.pick(5, 5)
    expect(name, ent is None and pid == 0)


def test_pick_decodes_id():
    name = "test_pick_decodes_id"
    mock_gl_success()
    gl.glReadPixels = lambda *a: bytes([5, 0, 0])
    ps = PickingSystem(10, 10)
    ps.init()
    ps.id_to_entity[5] = "Cube"
    ent, pid = ps.pick(0, 0)
    expect(name, ent == "Cube" and pid == 5)


def test_pick_clamps_coords():
    name = "test_pick_clamps_coords"
    mock_gl_success()
    gl.glReadPixels = lambda *a: bytes([1, 0, 0])
    ps = PickingSystem(10, 10)
    ps.init()
    try:
        ps.pick(-100, 999)
        ok(name)
    except Exception as e:
        fail(name, str(e))


def test_mouse_click_detected():
    name = "test_mouse_click_detected"
    ps = PickingSystem(10, 10)
    sdl2.SDL_GetMouseState = mock_get_mouse_state

    mock_mouse_sequence([
        (0, 10, 20),
        (sdl2.SDL_BUTTON_LMASK, 10, 20),
    ])

    ps.check_for_click()  # first frame
    res = ps.check_for_click()  # transition

    expect(name, res == (10, 20))


def test_mouse_hold_no_repeat():
    name = "test_mouse_hold_no_repeat"
    ps = PickingSystem(10, 10)
    sdl2.SDL_GetMouseState = mock_get_mouse_state

    mock_mouse_sequence([
        (sdl2.SDL_BUTTON_LMASK, 1, 1),
        (sdl2.SDL_BUTTON_LMASK, 1, 1),
    ])

    first = ps.check_for_click()
    second = ps.check_for_click()

    expect(name, first is not None and second is None)


def test_cleanup_resets_handles():
    name = "test_cleanup_resets_handles"
    mock_gl_success()
    ps = PickingSystem(10, 10)
    ps.init()
    ps.cleanup()
    expect(name, ps.fbo is None and ps.tex_color is None and ps.rbo_depth is None)


# -------------------------
# RUN ALL
# -------------------------

if __name__ == "__main__":
    test_init_fbo()
    test_resize_updates_dimensions()
    test_camera_matrix_set()
    test_begin_resets_ids()
    test_pick_zero_returns_none()
    test_pick_decodes_id()
    test_pick_clamps_coords()
    test_mouse_click_detected()
    test_mouse_hold_no_repeat()
    test_cleanup_resets_handles()
    print("Tests completed.")