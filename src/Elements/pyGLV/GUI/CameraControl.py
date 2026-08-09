"""
Pure camera-math helpers used by Elements.pyGLV.GUI.Viewer.RenderDecorator's updateCamera()
(shift/ctrl+right-drag pan/dolly, and Entity-based cameras) and freeLookAndFly()
(right-button-held look/fly).

Every function below takes plain arrays/dicts/scalars and returns plain arrays -- no `self`, no
window/event-system coupling -- so the actual camera math can be read and reasoned about (or
tested) independently of the Decorator/GUI machinery that calls it.

The two eye/target pairs are deliberate opposites: compute_free_camera_step() swings the *eye*
around a stationary target (orbit), while compute_look_step() swings the *target* around a
stationary eye (free-look).
"""

from __future__ import annotations

import numpy as np

import Elements.pyECSS.math_utilities as util

#: default speed for the free eye/target/up camera (compute_free_camera_step)
FREE_CAMERA_SPEED = 0.2

#: default speed for the Entity-based camera (compute_entity_camera_step)
ENTITY_CAMERA_SPEED = 5

#: degrees the look direction swings per pixel of right-drag (compute_look_step)
LOOK_SENSITIVITY = 0.15

#: starting world-units-per-frame for the WASD/QE fly controls (compute_fly_step). One value can't
#: suit every scene -- examples frame their cameras anywhere from ~1 unit off the target -- so
#: this is only the starting point: RenderDecorator.flySpeed is adjustable at runtime by scrolling
#: with the right button held.
FLY_SPEED = 0.05

#: multiplier applied per scroll notch when adjusting flySpeed. Multiplicative, not additive: the
#: useful range spans an order of magnitude between examples, which a fixed increment would step
#: through far too coarsely at the bottom and too finely at the top.
FLY_SPEED_SCROLL_STEP = 1.10

#: bounds for the runtime-adjusted flySpeed, in world units per frame
MIN_FLY_SPEED = 0.001
MAX_FLY_SPEED = 5.0

#: how close (in degrees) the look direction may get to +up/-up before pitch stops. Looking
#: exactly along up makes cross(forward, up) zero, which degenerates lookat()'s basis.
MIN_POLAR_ANGLE = 2.0


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


def _rotate_direction(direction, axis, degrees: float) -> np.ndarray:
    """`direction` rotated about `axis` by `degrees`, right-hand rule (util.rotate's convention).
    The appended 0 -- rather than 1 -- is what keeps this a direction: util.rotate returns a 4x4,
    and w=0 makes any translation in it a no-op."""
    rotated = util.rotate(axis, degrees) @ np.append(direction, [0.0])
    return util.normalise(rotated[:3])


def compute_look_step(
    eye,
    target,
    up,
    dragX: float,
    dragY: float,
    sensitivity: float = LOOK_SENSITIVITY,
) -> np.ndarray:
    """
    One step of mouse free-look: swing the look direction around a *stationary* eye. Returns the
    new target only -- eye and up are untouched, which is the whole point of this path.

    dragX/dragY are a right-drag delta exactly as both window backends report it from
    poll_right_drag_delta() (x already negated, y growing downward), so dragging right looks right
    and dragging down looks down.

    Eye-to-target distance is preserved, so an orbit/pan afterwards (compute_free_camera_step)
    still pivots about a point the same distance ahead, rather than about wherever the last
    free-look happened to leave the target.
    """
    teye = np.array(eye, dtype=np.float64)
    ttarget = np.array(target, dtype=np.float64)
    tup = util.normalise(np.array(up, dtype=np.float64))

    offset = ttarget - teye
    distance = np.linalg.norm(offset)
    if distance < 1e-8:
        return ttarget  # eye and target coincide: there is no look direction to swing
    forward = offset / distance

    # Yaw about `up`. rotate() is right-handed and rightDir is cross(forward, up), so a positive
    # angle swings the look direction *left*; dragX arrives already negated by
    # poll_right_drag_delta(), which cancels out to "drag right, look right".
    forward = _rotate_direction(forward, tup, sensitivity * dragX)

    # Pitch about the *post-yaw* screen-right axis, and only if it keeps the look direction clear
    # of the up/-up poles -- otherwise this step is dropped and the yaw alone applies.
    rightDir = util.normalise(np.cross(forward, tup))
    pitched = _rotate_direction(forward, rightDir, -sensitivity * dragY)
    if abs(np.dot(pitched, tup)) < np.cos(np.radians(MIN_POLAR_ANGLE)):
        forward = pitched

    return teye + forward * distance


def compute_fly_step(
    eye,
    target,
    up,
    forwardAxis: float,
    rightAxis: float,
    upAxis: float,
    speed: float = FLY_SPEED,
) -> tuple[np.ndarray, np.ndarray]:
    """
    One step of the WASD/QE fly controls. Returns the new (eye, target): both move by the *same*
    offset, which is what keeps the look direction fixed while the position changes.

    forwardAxis/rightAxis/upAxis are each -1, 0 or +1. Forward is the full 3D look direction, so W
    flies along it (including its vertical component) rather than walking the ground plane.

    RenderDecorator drives this with W/A/S/D only, passing upAxis=0: Q/E go through
    compute_rise_step() instead, which moves the eye against a fixed target. The vertical axis
    stays available here for any caller that wants a true look-direction-preserving lift.
    """
    teye = np.array(eye, dtype=np.float64)
    ttarget = np.array(target, dtype=np.float64)
    tup = util.normalise(np.array(up, dtype=np.float64))

    forwardDir = util.normalise(ttarget - teye)
    rightDir = util.normalise(np.cross(forwardDir, tup))

    offset = speed * (forwardAxis * forwardDir + rightAxis * rightDir + upAxis * tup)
    return teye + offset, ttarget + offset


def compute_rise_step(
    eye,
    target,
    up,
    upAxis: float,
    speed: float = FLY_SPEED,
) -> np.ndarray:
    """
    One step of the Q/E rise/sink controls. Returns the new eye only: the target stays exactly
    where it is, so the camera tilts to keep looking at the same point as it climbs or drops.

    That is the deliberate difference from compute_fly_step(), which carries the target along and
    so preserves the look direction instead. Rising with a fixed target eventually puts the eye
    directly above it, where the look direction is parallel to `up` and cross(forward, up)
    collapses -- so the step that would reach (or pass) that pole is refused, and the eye stays
    where it was, exactly as compute_look_step() clamps pitch.
    """
    teye = np.array(eye, dtype=np.float64)
    ttarget = np.array(target, dtype=np.float64)
    tup = util.normalise(np.array(up, dtype=np.float64))

    candidate = teye + speed * upAxis * tup

    offset = ttarget - candidate
    distance = np.linalg.norm(offset)
    if distance < 1e-8:
        return teye  # the step would land the eye on the target itself

    if abs(np.dot(offset / distance, tup)) > np.cos(np.radians(MIN_POLAR_ANGLE)):
        return teye  # would reach straight-above/below the target

    return candidate


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
    One step of the Entity-based camera: rotate/translate a
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
