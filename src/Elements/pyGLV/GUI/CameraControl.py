"""
Pure camera-math helpers used by Elements.pyGLV.GUI.Viewer.RenderDecorator.updateCamera().

Both functions below take plain arrays/dicts/scalars and return plain arrays -- no `self`, no
window/event-system coupling -- so the actual camera math can be read and reasoned about (or
tested) independently of the Decorator/GUI machinery that calls it.
"""

from __future__ import annotations

import numpy as np

import Elements.pyECSS.math_utilities as util

#: default speed for the free eye/target/up camera (compute_free_camera_step)
FREE_CAMERA_SPEED = 0.2

#: default speed for the Entity-based camera (compute_entity_camera_step)
ENTITY_CAMERA_SPEED = 5


def compute_free_camera_step(
    eye,
    target,
    up,
    translation: dict,
    rotation: dict,
    moveX: bool,
    moveY: bool,
    moveZ: bool,
    rotateX: bool,
    rotateY: bool,
    cameraspeed: float = FREE_CAMERA_SPEED,
) -> tuple[np.ndarray, np.ndarray]:
    """
    One step of the free eye/target/up camera (orbit/pan/zoom) -- used whenever a scene has no
    Entity-based camera to orbit instead (see RenderDecorator.traverseCamera()/self.cam). Returns
    the new (eye, target); `up` itself is never changed by this path.
    """
    teye = np.array(eye, dtype=np.float64)
    ttarget = np.array(target, dtype=np.float64)
    tup = np.array(up, dtype=np.float64)

    forwardDir = util.normalise(ttarget - teye)
    rightDir = util.normalise(np.cross(forwardDir, tup))

    if rotateX:
        rotMatY = util.rotate(tup, rotation["x"] * cameraspeed * 15)
        transMatY = util.translate(ttarget) @ rotMatY @ util.translate(-ttarget)
        teye = transMatY @ np.append(teye, [1])
        teye = teye[:-1] / teye[-1]
    elif rotateY:
        rotMatX = util.rotate(rightDir, -rotation["y"] * cameraspeed * 15)
        transMatX = util.translate(ttarget) @ rotMatX @ util.translate(-ttarget)
        teye = transMatX @ np.append(teye, [1])
        teye = teye[:-1] / teye[-1]
    elif moveX or moveY:
        panX = -cameraspeed * translation["x"] * rightDir
        panY = -translation["y"] * cameraspeed * tup
        teye = teye + panX + panY
        ttarget = ttarget + panX + panY
    elif moveZ:
        zoom = np.sign(translation["z"]) * cameraspeed * forwardDir
        teye = teye + zoom
        ttarget = ttarget + zoom

    return teye, ttarget


def compute_entity_camera_step(
    trs: np.ndarray,
    translation: dict,
    rotation: dict,
    moveX: bool,
    moveY: bool,
    moveZ: bool,
    rotateX: bool,
    rotateY: bool,
    cameraspeed: float = ENTITY_CAMERA_SPEED,
) -> np.ndarray:
    """
    One step of the Entity-based camera (examples 7-11 and pyJANVRED): rotate/translate a
    BasicTransform's own `trs` matrix directly, rather than an eye/target/up pair. Returns the new
    `trs`.
    """
    if rotateX:
        rotMatY = util.rotate((0, 1, 0), rotation["x"] * cameraspeed)
        trs = rotMatY @ trs
    elif rotateY:
        rotMatX = util.rotate((1, 0, 0), -rotation["y"] * cameraspeed)
        trs = trs @ rotMatX

    if moveX or moveY or moveZ:
        transMat = util.translate(translation["x"], translation["y"], -translation["z"])
        trs = trs @ transMat

    return trs
