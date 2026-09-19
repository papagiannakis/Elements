"""
generateTerrain convenience method, part of Elements.pyGLV
    
Elements.pyGLV (Computer Graphics for Deep Learning and Scientific Visualization)
@Copyright 2021-2022 Dr. George Papagiannakis
    
Convenience method for scene wireframe terrain generation

The terrain is a ground reference on the y=0 plane, centred on the world origin: it exists to show
where (0,0,0) and "the floor" are while navigating a scene. Because the 2*N+1 line positions are
spread symmetrically over [-size, size], the middle line of each direction sits exactly on x=0 and
z=0, so two of the grid lines cross at the origin.

The optional sizeX/sizeZ arguments add the two upright planes through the origin (x=0 and z=0),
which together with the ground give a full three-plane corner to judge height against, not just
position on the floor.

"""

import numpy as np


def _resolveN(size, N):
    """N as given, or -- when N<=0 -- the value that makes the grid cells 1 unit across.

    2*N+1 lines cut the 2*size span into 2*N cells, so a cell is size/N across and N=size is what
    puts the lines exactly 1 apart. floor() keeps N whole; for an integer `size` that is exact, and
    for a fractional one the cells stretch a little past 1 rather than the grid stopping short of
    the extent that was asked for. Never below 1, so a size under 1 still yields a grid."""
    if N > 0:
        return N
    return max(1, int(np.floor(size)))


def _gridLevels(low, high, step):
    """Heights from `low` upwards at `step` spacing, always closed off with `high` itself.

    `high` is appended explicitly because a plane's height rarely divides evenly by the ground
    grid's spacing: without it the topmost row of squares would be left open, and the plane would
    stop visibly short of the extent it was asked for. That last row is the short one."""
    levels = list(np.arange(low, high, step))
    if not levels or abs(levels[-1] - high) > 1e-9:
        levels.append(high)
    return levels


def _uprightPlaneLines(extent, across, step, place):
    """Endpoint pairs for one upright grid plane, or [] if `extent` has no height.

    `extent` is the plane's (y) range, `across` the horizontal positions it shares with the ground
    grid -- shared so the two grids line up where they meet -- and `place(h, v)` maps a
    (horizontal, vertical) pair onto the plane in world space."""
    low, high = min(extent), max(extent)
    if high - low <= 0:
        return []

    points = []
    for v in _gridLevels(low, high, step):
        # line at constant height, running the full width of the plane
        points.append(place(across[0], v))
        points.append(place(across[-1], v))
    for h in across:
        # line at constant horizontal position, running the plane's full height
        points.append(place(h, low))
        points.append(place(h, high))
    return points


def generateTerrain(size=5,N=0,uniform_color = [0.4,0.4,0.4,0.5],sizeX = [0,0],sizeZ = [0,0]):
    """(vertices, indices, colors) for a square grid of lines on y=0, to be drawn with
    VertexArray(primitive=GL_LINES).

    The grid spans [-size, size] in x and z, with 2*N+1 lines each way. N=0 (the default) picks N
    from `size` instead, so that the cells come out 1 unit across -- see _resolveN().

    A grid of squares needs no per-square geometry at all: 2*N+1 full-width lines crossing 2*N+1
    full-depth ones *are* the squares. So this emits one segment per grid line -- two endpoints,
    2*size long, spanning the whole terrain -- rather than chopping each line into 2*N pieces at the
    intersections. Nothing needs a vertex where two lines cross; they simply overlap on screen.

    That is 4*(2*N+1) vertices instead of (2*N+1)**2: 44 rather than 121 at the default size=5.

    sizeX and sizeZ optionally add the two upright grid planes through the origin. Both give a
    *vertical* (y) range -- the horizontal extent is inherited from `size`, so each plane shares its
    across-lines with the ground grid and the two meet exactly where they cross:

      sizeX=[y1,y2]  the x=0 plane, spanning z in [-size, size], e.g. its far line runs
                     [0,y1,size] -> [0,y2,size]
      sizeZ=[y1,y2]  the z=0 plane, spanning x in [-size, size], e.g. its far line runs
                     [size,y1,0] -> [size,y2,0]

    [0,0] (the default) or any zero-height range leaves that plane out; a reversed range is read
    low-to-high. The upright planes are subdivided at the ground grid's own spacing rather than into
    2*N+1 rows, so their cells stay square instead of being squashed by a short height.
    """
    N = _resolveN(size, N)
    x = np.linspace(-size,size,2*N+1)
    #: spacing between neighbouring lines of `x`, reused by the upright planes
    step = size/N
    points = []

    for xi in x:
        # line at constant x, running the full depth in z
        points.append([xi,0,-size])
        points.append([xi,0, size])

    for zi in x:
        # line at constant z, running the full width in x
        points.append([-size,0,zi])
        points.append([ size,0,zi])

    # the x=0 plane spans z horizontally, the z=0 plane spans x -- hence which slot `h` fills
    points += _uprightPlaneLines(sizeX, x, step, lambda h, v: [0.0, v, h])
    points += _uprightPlaneLines(sizeZ, x, step, lambda h, v: [h, v, 0.0])

    # GL_LINES consumes the vertices in pairs, and they are already laid out as endpoint pairs, so
    # the indices are simply their own order. (VertexArray would also draw this with no index buffer
    # at all, but every caller passes one to RenderMesh.vertex_index.)
    indices = np.arange(len(points),dtype=np.uint32)

    #colors

    colorT = [uniform_color]*len(points)
    return np.array(points,dtype=np.float32) , indices, np.array(colorT, dtype=np.float32)

if __name__ == "__main__":
    ps, ind, col = generateTerrain()
    print (ps, ind)
