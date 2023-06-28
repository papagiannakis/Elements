"""
Utilities and helper functions for basic computer graphics linear/quaternion algebra 
& real-time rendering components
    
Elements.pyECSS (Entity Component Systems in a Scenegraph) package
@Copyright 2021-2022 Dr. George Papagiannakis
    
Most methods have been tested against glm equivalent methods: 
https://github.com/Zuzu-Typ/PyGLM/tree/master/wiki/function-reference

"""

# Python built-in modules
import math
from numbers import Number
from numpy.linalg import inv

# Python external modules
import numpy as np
from trimesh import Scene


# vector, points related functions -----------------------------------------------
def vec(*iterable):
    """
    return a numpy vector out of any iterable (list, tuple...) as column-major ('F')
    """
    return np.asarray(iterable if len(iterable) > 1 else iterable[0],dtype=np.float32, order='F')

def normalise(vector):
    """standard vector normalization over any numpy array

    :param vector: iterable vector to normalise
    :type vector: numpy array
    """

    if isinstance(vector, np.ndarray)==False:
        vector = vec(vector)
    norm = np.linalg.norm(vector,2) #equivalent to norm = np.sqrt(np.sum(vector**2))
    return vector / norm if norm >0. else vector

def lerp(point_a, point_b, fraction):
    """standard linear interpolation between two vectors and a fraction value

    :param point_a: first point
    :type point_a: numpy array
    :param point_b: second point
    :type point_b: numpy array
    :param fraction: value t
    :type fraction: float from 0.0 to 1.0
    :return: linearly interpolated value
    :rtype: numpy array
    """
    
    if isinstance(point_a, np.ndarray)==False:
        point_a = vec(point_a)
    if isinstance(point_b, np.ndarray)==False:
        point_b = vec(point_b)
    try:
        fraction = float(fraction)
    except ValueError:
        print (f'HEY! {fraction} is not a float!')
    
    return point_a + fraction * (point_b - point_a)

def calculateNormals(p1, p2, p3):
    vector1 = np.array(p1);
    vector2 = np.array(p2);
    vector3 = np.array(p3);

    U = vector2 - vector1;
    V = vector3 - vector1;
    
    normal = [0, 0, 0, 1];
    normal[0] = (U[1] * V[2]) - (U[2] * V[1])
    normal[1] = (U[2] * V[0]) - (U[0] * V[2])
    normal[2] = (U[0] * V[1]) - (U[1] * V[0])

    return normal;

def distance(point_a, point_b):
    return math.sqrt(
        math.pow((point_b[0] - point_a[0]), 2) +
        math.pow((point_b[1] - point_a[1]), 2) +
        math.pow((point_b[2] - point_a[2]), 2)
    );

# ------------ convenience CG functions for vector, matrix and camera transformations --------------

def identity(rank=4):
    """generate a numpy identity matrix

    :param rank: [description], defaults to 4 for 4x4 matrix, otherwise 3 for 3x3 or 2 for 2x2
    :type rank: int, optional
    """
    if(rank == 4):
        return np.identity(4)
    elif (rank == 3):
        return np.identity(3)
    elif (rank == 2):
        return np.identity(2)
    elif (rank < 2 and rank > 4):
        return np.identity(4)
    
def inverse(matrix):
    """call numpy linalg.inv(a)[source] to compute the inverse of a numpy matrix

    :param matrix: [description]
    :type matrix: [type]
    """
    if isinstance(matrix, np.ndarray):
        return inv(matrix)
    
def ortho(left, right, bottom, top, near, far):
    """ Orthographic projection matrix creation function, where 
    the viewing volume is a rectangular parallelepiped, or more informally, a box. 
    Original projection matrices defined in http://www.glprogramming.com/red/appendixf.html
    and in http://www.glprogramming.com/red/chapter03.html. Tested also again glm similar 
    functions.
    For more on projections check: http://www.opengl-tutorial.org/beginners-tutorials/tutorial-3-matrices/ 
    
    :param left: [coordinates of projection unit cube]
    :type left: [float]
    :param right: [coordinates of projection unit cube]
    :type right: [float]
    :param bottom: [coordinates of projection unit cube]
    :type bottom: [float]
    :param top: [coordinates of projection unit cube]
    :type top: [float]
    :param near: [coordinates of near clipping plane]
    :type near: [float]
    :param far: [coordinates of far clipping plane]
    :type far: [float]
    """
    dx, dy, dz = right - left, top - bottom, far - near
    rx, ry, rz = -(right+left) / dx, -(top+bottom) / dy, -(far+near) / dz
    return np.array([
                    [2/dx, 0,    0,     rx],
                     [0,    2/dy, 0,     ry],
                     [0,    0,    -2/dz, rz],
                     [0,    0,    0,     1]
                     ], dtype=np.float32,order='F')
    
def perspective(fovy, aspect, near, far):
    """Perspective projection matrix creation function, where 
    the viewing volume is a truncated pyramid. 
    Original projection matrices defined in http://www.glprogramming.com/red/appendixf.html
    and in http://www.glprogramming.com/red/chapter03.html and 
    https://www.khronos.org/registry/OpenGL-Refpages/gl2.1/xhtml/gluPerspective.xml 
    Tested also again glm similar functions.

    :param fovy: [description]
    :type fovy: [type]
    :param aspect: [description]
    :type aspect: [type]
    :param near: [description]
    :type near: [type]
    :param far: [description]
    :type far: [type]
    """
    _scale = 1.0/math.tan(math.radians(fovy)/2.0)

    sx, sy = _scale / aspect, _scale
    zz = (far + near) / (near - far)
    zw = 2 * far * near/(near - far)
    return np.array([[sx, 0,  0,  0],
                     [0,  sy, 0,  0],
                     [0,  0, zz, zw],
                     [0,  0, -1,  0]], dtype=np.float32,order='F')
    
def frustum(xmin, xmax, ymin, ymax, zmin, zmax):
    """Alternative Perspective projection matrix creation function, where 
    the viewing volume is a truncated pyramid. 
    Original projection matrices defined in http://www.glprogramming.com/red/appendixf.html
    and in http://www.glprogramming.com/red/chapter03.html and 
    https://www.khronos.org/registry/OpenGL-Refpages/gl2.1/xhtml/gluPerspective.xml 
    Tested also again glm similar functions.

    :param xmin: [description]
    :type xmin: [type]
    :param xmax: [description]
    :type xmax: [type]
    :param ymin: [description]
    :type ymin: [type]
    :param ymax: [description]
    :type ymax: [type]
    :param zmin: [description]
    :type zmin: [type]
    :param zmax: [description]
    :type zmax: [type]
    """
    a = (xmax+xmin) / (xmax-xmin)
    b = (ymax+ymin) / (ymax-ymin)
    c = -(zmax+zmin) / (zmax-zmin)
    d = -2*zmax*zmin / (zmax-zmin)
    sx = 2*zmin / (xmax-xmin)
    sy = 2*zmin / (ymax-ymin)
    return np.array([[sx, 0,  a, 0],
                     [0, sy,  b, 0],
                     [0,  0,  c, d],
                     [0,  0, -1, 0]], dtype=np.float32,order='F')
    

def translate(x=0.0, y=0.0, z=0.0):
    """ Convert a euclidean translation vector in homogeneous coordinates to a 
    standard 4x4 Translation Transformation matrix based on the original OpenGL formulas defined in:
    http://www.glprogramming.com/red/appendixf.html and OpenGL 1.0 specification. 
    The matrix will be created either from 3 euclidean coordinates or a vector x: vec(x)

    :param x: [description], defaults to 0.0
    :type x: float, optional or vec
    :param y: [description], defaults to 0.0
    :type y: float, optional
    :param z: [description], defaults to 0.0
    :type z: float, optional
    """
    Tmat = np.identity(4, np.float32)

    if isinstance(x, Number):
        Tmat[:3,3] = vec(x,y,z)  #slicing is [start:end:step], :3,3 = all 3 rows on 3 column
    else:
         Tmat[:3,3] = vec(x)
    
    return Tmat



def scale(x, y=None, z=None):
    """Convert a euclidean scaling vector in homogeneous coordinates to a 
    standard 4x4 Scaling Transformation matrix based on the original OpenGL formulas defined in:
    http://www.glprogramming.com/red/appendixf.html and OpenGL 1.0 specification. 
    The matrix will be created either from 3 euclidean coordinates for scaling in 3 dimensions 
    or a vector x: vec(x) for uniform scaling across x,y,z dimensions

    :param x: [description], defaults to 1.0
    :type x: float, optional
    :param y: [description], defaults to None
    :type y: [type], optional
    :param z: [description], defaults to None
    :type z: [type], optional
    """
    x, y, z = (x, y, z)  if isinstance(x, Number) else (x[0], x[1], x[2])
    y, z = (x, x) if y is None or z is None else (y, z) # case of uniform scaling if y, z are None
    return np.diag((x, y, z, 1))


def sincos(degrees=0.0, radians=None):
    """Utility function to calculate with one call sine and cosine of an angle in radians or degrees
    If there is one argument, then assumes that single input is in degrees, 
    otherwise ignores first value and takes second for radians (needs two in that case)
    It returns the value in radians, first sin then cos
    
    :param degrees: [description], defaults to 0.0
    :type degrees: float, optional
    :param radians: [description], defaults to None
    :type radians: [type], optional
    """
    radians = radians if radians else math.radians(degrees)
    return math.sin(radians), math.cos(radians) 

def rotate(axis=(1.0,0.0,0.0), angle=0.0, radians=None):
    """From a euclidean axis vector and a rotation angle, generate a 
    standard 4x4 Rotation Transformation matrix based on the original OpenGL formulas defined in:
    http://www.glprogramming.com/red/appendixf.html and axis-angle theoretical matrix specification:
    https://en.wikipedia.org/wiki/Rotation_matrix  

    :param axis: [vector3], defaults to (1.0,0.0,0.0)
    :type axis: tuple, optional
    :param angle: [degrees], defaults to 0.0
    :type angle: float, optional
    :param radians: [rads], defaults to None
    :type radians: [float], optional
    """
    x, y, z = normalise(vec(axis))
    s, c = sincos(angle, radians)
    nc = 1 - c
    return np.array([[x*x*nc + c,   x*y*nc - z*s, x*z*nc + y*s, 0],
                     [y*x*nc + z*s, y*y*nc + c,   y*z*nc - x*s, 0],
                     [x*z*nc - y*s, y*z*nc + x*s, z*z*nc + c,   0],
                     [0,            0,            0,            1]], dtype=np.float32,order='F')
    

def lookat(eye, target, up):
    """Utility function to calculate a 4x4 camera lookat matrix, based on the eye, target and up camera vectors:
    based on the gluLookAt() convenience method of https://www.khronos.org/registry/OpenGL-Refpages/gl2.1/xhtml/gluLookAt.xml
    and the implementation of https://github.com/g-truc/glm/blob/master/glm/ext/matrix_transform.inl
    and https://github.com/Zuzu-Typ/PyGLM/blob/master/wiki/function-reference/stable_extensions/matrix_transform.md#lookAt-function 
        
    :param eye: [description]
    :type eye: [type]
    :param target: [description]
    :type target: [type]
    :param up: [description]
    :type up: [type]
    """
 
    _eye = np.array(eye)
    _target = np.array(target)
    _up = np.array(up)

    def normalise(x):
        return x/np.linalg.norm(x)

    # # lookAtRH
    _f = normalise(_target - _eye) 
    _s = normalise(np.cross(_f,_up))
    _u = np.cross(_s,_f) 
    M = np.identity(4)
    M[0,0] = _s[0]
    M[0,1] = _s[1]
    M[0,2] = _s[2]
    M[1,0] = _u[0]
    M[1,1] = _u[1]
    M[1,2] = _u[2]
    M[2,0] = -_f[0]
    M[2,1] = -_f[1]
    M[2,2] = -_f[2]
    M[0,3] = -np.dot(_s, _eye)
    M[1,3] = -np.dot(_u, _eye)
    M[2,3] =  np.dot(_f, _eye)

    return M


def lookatLH(eye, target, up):
    """Utility function to calculate a 4x4 camera lookat matrix, based on the eye, target and up camera vectors:
    based on the gluLookAt() convenience method of https://www.khronos.org/registry/OpenGL-Refpages/gl2.1/xhtml/gluLookAt.xml
    and the implementation of https://github.com/g-truc/glm/blob/master/glm/ext/matrix_transform.inl
    and https://github.com/Zuzu-Typ/PyGLM/blob/master/wiki/function-reference/stable_extensions/matrix_transform.md#lookAt-function 
        
    :param eye: [description]
    :type eye: [type]
    :param target: [description]
    :type target: [type]
    :param up: [description]
    :type up: [type]
    """
 
    _eye = np.array(eye)
    _target = np.array(target)
    _up = np.array(up)

    def normalise(x):
        return x/np.linalg.norm(x)

    # lookAtLH
    _f = normalise(_target - _eye) 
    _s = normalise(np.cross(_up, _f))
    

    _u = np.cross(_f, _s) 
    M = np.identity(4)
    M[0,0] = _s[0]
    M[0,1] = _s[1]
    M[0,2] = _s[2]
    M[1,0] = _u[0]
    M[1,1] = _u[1]
    M[1,2] = _u[2]
    M[2,0] = _f[0]
    M[2,1] = _f[1]
    M[2,2] = _f[2]
    M[0,3] = -np.dot(_s, _eye)
    M[1,3] = -np.dot(_u, _eye)
    M[2,3] = -np.dot(_f, _eye)
    
    return M
# -------------------- quaternion algebra convenience functions ----------------------

#quaternion()
def quaternion(x=vec(0.0, 0.0, 0.0, 0.0), y=0.0, z=0.0, w=1.0):
    """Generate a quaternion array from 4 values or a vec3 for vector and w for scalar parts (scalar-last list scipy)
    It has been tested against: 
    https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.transform.Rotation.html#scipy.spatial.transform.Rotation 

    :param x: [description], defaults to vec(0.0, 0.0, 0.0, 0.0)
    :type x: [type], optional
    :param y: [description], defaults to 0.0
    :type y: float, optional
    :param z: [description], defaults to 0.0
    :type z: float, optional
    :param w: [description], defaults to 1.0
    :type w: float, optional
    """
    x, y, z = (x, y, z) if isinstance(x, Number) else (x[0], x[1], x[2])
    return np.array([x, y, z, w], dtype=np.float32,order='F') 


def quaternion_from_axis_angle(axis:vec, degrees=0.0, radians=None):
    """Generate a quaternion from a rotation axis and an angle, scalar-last like scipy
    # https://www.euclideanspace.com/maths/geometry/rotations/conversions/angleToQuaternion/index.htm 
    # https://en.wikipedia.org/wiki/Axis–angle_representation#Rotation_vector 

    :param axis: [description]
    :type axis: vec
    :param degrees: [description], defaults to 0.0
    :type degrees: float, optional
    :param radians: [description], defaults to None
    :type radians: [type], optional
    """
    sin, cos = sincos(radians * 0.5) if radians else sincos(degrees * 0.5)
    return quaternion(normalise(vec(axis)) * sin, w=cos)

def quaternion_from_euler(pitch=0.0, yaw=0.0, roll=0.0, radians=None):
    """Create a quaternion out of euler angles (pitch = x, yaw = y, roll = z), scalar-last like scipy
    https://www.euclideanspace.com/maths/geometry/rotations/conversions/eulerToQuaternion/index.htm
    
    :param yaw: [description], defaults to 0.0
    :type yaw: float, optional
    :param pitch: [description], defaults to 0.0
    :type pitch: float, optional
    :param roll: [description], defaults to 0.0
    :type roll: float, optional
    :param radians: [description], defaults to None
    :type radians: [type], optional
    """
    siy, coy = sincos(yaw * 0.5, radians[0] * 0.5 if radians else None)
    sir, cor = sincos(roll * 0.5, radians[1] * 0.5 if radians else None)
    sip, cop = sincos(pitch * 0.5, radians[2] * 0.5 if radians else None)
    return quaternion(x=coy*sir*cop - siy*cor*sip, y=coy*cor*sip + siy*sir*cop,
                      z=siy*cor*cop - coy*sir*sip, w=coy*cor*cop + siy*sir*sip)


def quaternion_mul(q1, q2):
    """Compute and return a new quaternion which is the product of two quaternions, scalar-last like scipy
    https://www.euclideanspace.com/maths/algebra/realNormedAlgebra/quaternions/arithmetic/index.htm

    :param q1: [description]
    :type q1: [type]
    :param q2: [description]
    :type q2: [type]
    """
    return np.dot(np.array([
                            [q1[1],  q1[0], -q1[3],  q1[2]],
                            [q1[2],  q1[3],  q1[0], -q1[1]],
                            [q1[3], -q1[2],  q1[1],  q1[0]],
                            [q1[0], -q1[1], -q1[2], -q1[3]]
                            ],dtype=np.float32,order='F'), q2)
                        

def quaternion_matrix(q):
    """Compute and return a 4x4 matrix from the quaternion q, scalar-last like scipy
    https://www.euclideanspace.com/maths/geometry/rotations/conversions/quaternionToMatrix/index.htm 

    :param q: [description]
    :type q: [type]
    """
    q = normalise(q)  # only unit quaternions are valid rotations.
    nxx, nyy, nzz = -q[1]*q[1], -q[2]*q[2], -q[3]*q[3]
    qwx, qwy, qwz = q[0]*q[1], q[0]*q[2], q[0]*q[3]
    qxy, qxz, qyz = q[1]*q[2], q[1]*q[3], q[2]*q[3]
    return np.array([
                    [2*(nyy + nzz)+1, 2*(qxy - qwz),   2*(qxz + qwy),   0],
                     [2 * (qxy + qwz), 2 * (nxx + nzz) + 1, 2 * (qyz - qwx), 0],
                     [2 * (qxz - qwy), 2 * (qyz + qwx), 2 * (nxx + nyy) + 1, 0],
                     [0, 0, 0, 1] 
                     ], dtype=np.float32,order='F')
    

def quaternion_slerp(q0, q1, fraction):
    """Spherical linear interpolation from unit q0 to unit q1 based on fraction f:
    https://en.wikipedia.org/wiki/Slerp#Quaternion_Slerp 
    https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.transform.Slerp.html#scipy.spatial.transform.Slerp 
    http://number-none.com/product/Understanding%20Slerp,%20Then%20Not%20Using%20It/ 
    
    :param q0: [description]
    :type q0: [type]
    :param q1: [description]
    :type q1: [type]
    :param fraction: [description]
    :type fraction: [type]
    """
    # only unit quaternions are valid rotations.
    q0, q1 = normalise(q0), normalise(q1)
    # Compute the cosine of the angle between the two vectors.
    dot = np.dot(q0, q1)
    
    # if the inputs are too close, linearly interpolate and normalize the result
    DOT_THRESHOLD = 0.9995
    if dot > DOT_THRESHOLD:
        quat_result = q0 + fraction * (q1 -q0)
        return normalise(quat_result)

    # if negative dot product, the quaternions have opposite handedness
    # and slerp won't take the shorter path. Fix by reversing one quaternion.
    q1, dot = (q1, dot) if dot > 0 else (-q1, -dot)

    theta_0 = math.acos(np.clip(dot, -1, 1))  # angle between input vectors
    theta = theta_0 * fraction                # angle between q0 and result
    q2 = normalise(q1 - q0*dot)              # {q0, q2} now orthonormal basis

    return   q0*math.cos(theta) + q2*math.sin(theta)

