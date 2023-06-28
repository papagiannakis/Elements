import sys

sys.path.append("../../../")
import clifford.g3c as cga
import clifford.pga as pga
import clifford as cl

import numpy as np

import Elements.pyECSS.utilities as util
from Elements.pyECSS.GA.quaternion import Quaternion


###### CGA START ######

def t_q_to_TR(t, q):
    """
  Takes in a quaternion (q) and translation vector (t) and generates the respective CGA motor (TR)
  """
    T = 1 - 0.5 * (t[0] * cga.e1 + t[1] * cga.e2 + t[2] * cga.e3) * cga.einf
    R = q[3] - q[2] * cga.e12 + q[1] * cga.e13 - q[0] * cga.e23
    # print("T = ", T)
    # print("R = ", R)
    return T * R


def extract_t_q_from_TR(TR, algebra='CGA'):
    if algebra == 'CGA':
        T, R = extract_T_R_from_TR_CGA(TR)
        t = translator_cga_to_vector(T)
        q = rotor_cga_to_quaternion(R)
        return t, q
    else:
        T, R = extract_T_R_from_TR_PGA(TR)
        t = translator_pga_to_vector(T)
        q = rotor_pga_to_quaternion(R)
        return t, q


def extract_T_R_from_TR_CGA(TR):
    """
  Takes in a TR CGA motor and extracts the quaternion (q) and translation vector (t)
  """
    R = TR(cga.e123)
    T = (TR * ~R).normal()
    # print("T = ", T)
    # print("R = ", R)
    # tt = -2*(T|no)
    # t = [tt[cga.e1],tt[cga.e2],tt[cga.e3]]
    # q = [-R[cga.e23],R[cga.e13],-R[cga.e12],R.value[0]]
    return T, R


def translator_cga_to_vector(T):
    """
   Takes a cga translator and returns the corresponding vector t
   """
    no = -cga.eo
    tt = -2 * (T | no)
    return [tt[cga.e1], tt[cga.e2], tt[cga.e3]]


def rotor_cga_to_quaternion(R):
    """
   Takes a cga rotor and returns the corresponding quaternion q
   """
    return [-R[cga.e23], R[cga.e13], -R[cga.e12], R.value[0]]


def rotor_pga_to_quaternion(R):
    """
   Takes a pga rotor and returns the corresponding quaternion q
   """
    return [-R[pga.e23], R[pga.e13], -R[pga.e12], R.value[0]]


def matrix_to_angle_axis_translation(matrix):
    # taken from:   https://github.com/Wallacoloo/printipi/blob/master/util/rotation_matrix.py
    """Convert the rotation matrix into the axis-angle notation.
    Conversion equations
    ====================
    From Wikipedia (http://en.wikipedia.org/wiki/Rotation_matrix), the conversion is given by::
        x = Qzy-Qyz
        y = Qxz-Qzx
        z = Qyx-Qxy
        r = hypot(x,hypot(y,z))
        t = Qxx+Qyy+Qzz
        theta = atan2(r,t-1)
    @param matrix:  The 3x3 rotation matrix to update.
    @type matrix:   3x3 numpy array
    @return:    The 3D rotation axis and angle.
    @rtype:     numpy 3D rank-1 array, float
    """

    # Axes.
    axis = np.zeros(3, np.float64)
    axis[0] = matrix[2, 1] - matrix[1, 2]
    axis[1] = matrix[0, 2] - matrix[2, 0]
    axis[2] = matrix[1, 0] - matrix[0, 1]

    # Angle.
    r = np.hypot(axis[0], np.hypot(axis[1], axis[2]))
    t = matrix[0, 0] + matrix[1, 1] + matrix[2, 2]
    theta = np.arctan2(r, t - 1)
    # np.atan2
    # Normalise the axis.
    axis = axis / r

    # Return the data.
    if abs(theta) < 1e-6:
        axis = [1, 0, 0]

    return theta, axis, matrix[0:3, 3]


def matrix_to_motor(M, method='CGA'):
    "The matrix has to represent rotation and translation only, no scaling of x,y or z."
    if method == 'PGA':
        T, R = matrix_to_t_r_pga(M)
    else:
        T, R = matrix_to_t_r_cga(M)
    return T * R


def matrix_to_t_r_cga(M):
    "The matrix has to represent rotation and translation only, no scaling of x,y or z."
    phi, axis, trans = matrix_to_angle_axis_translation(M)
    if phi == 0 or np.isnan(axis[0]) or np.isnan(axis[1]) or np.isnan(axis[2]):
        R = 1
    else:
        # axis from euc to cga and normalization
        axis_cga = axis[0] * cga.e1 + axis[1] * cga.e2 + axis[2] * cga.e3
        axis_cga = axis_cga / np.linalg.norm(axis)
        I3_cga = cga.e1 * cga.e2 * cga.e3
        R = np.e ** (-(axis_cga * I3_cga) * (phi / 2))  # rotor

    # update trans from euclidean vector to  cga
    t = trans[0] * cga.e1 + trans[1] * cga.e2 + trans[2] * cga.e3
    T = np.e ** (-1 / 2 * t * cga.einf)  # translator
    return T, R


###### CGA END ######

# PGA below


def rotor_from_axis_angle_pga(axis, angle):
    "returns the pga multivector rotor that corresponds to rotation around axis=[x,y,z] by angle (in rads)"
    axis_pga = axis[0] * pga.e1 + axis[1] * pga.e2 + axis[2] * pga.e3
    u = axis_pga / np.linalg.norm(axis)
    I3_pga = pga.e1 * pga.e2 * pga.e3
    return np.cos(angle / 2) - u * I3_pga * np.sin(angle / 2)


#     return np.e**(-(u*I3_pga)*(angle/2))


def matrix_to_t_r_pga(M):
    "The matrix has to represent rotation and translation only, no scaling of x,y or z."
    angle, axis, trans = matrix_to_angle_axis_translation(M)
    if angle == 0 or np.isnan(axis[0]) or np.isnan(axis[1]) or np.isnan(axis[2]):
        R = 1
    else:
        R = rotor_from_axis_angle_pga(axis, angle)
    T = 1 - 1 / 2 * pga.e0 * (trans[0] * pga.e1 + trans[1] * pga.e2 + trans[2] * pga.e3)  # T = translator(trans)
    return T, R


def translator_pga_to_vector(T):
    """
   Takes a pga translator T and return the corresponding vector t
   """
    myT = T.normal()
    if myT.value[0] < 0: myT = -myT  # in case myT = -1 + ...
    return [-2 * myT[pga.e01], -2 * myT[pga.e02], -2 * myT[pga.e03]]


def extract_T_R_from_TR_PGA(TR):
    """
   Takes a PGA motor TR = T*R where T is a PGA translator and R is a PGA rotor and returns the
   t = translation vector
   q = the quaternion corresponding to the pga rotor
   """
    tmp = pga.e0 * TR
    R = tmp[pga.e0] + tmp[pga.e012] * pga.e12 + tmp[pga.e013] * pga.e13 + tmp[pga.e023] * pga.e23
    # we extracted the rotor R from the product TR
    T = (TR * ~R).normal()
    #  print("extracted R = ", R)
    #  print("extracted T = ", T)
    return T, R


def matrix_from_t_and_q(t, q):
    """
   Returns the TRS matrix corresponding to the translation vector t and quaternion q
   """
    M = np.zeros([4, 4])
    quat = Quaternion(q[0], q[1], q[2], q[3])
    M[:3, :3] = quat.to_rotation_matrix()
    M[:3, 3] = t
    return M


if __name__ == "__main__":
    print("=" * 20)
    print("GENERATE A TR MATRIX AND WRITE IT IN VARIOUS FORMS")
    print("=" * 20)
    theta = 30  # in degrees
    translation_vector = [1, 2, 3]
    axis = [1, 2, 3]
    M = util.translate(translation_vector) @ util.rotate(axis=axis, angle=theta)
    print("Original M:\n", M)

    print("Flatten M:")
    M_flatten = M.flatten()
    print(M_flatten)

    print("M in CGA multivector form:")
    M_CGA_array = matrix_to_motor(M, method='CGA').value
    print(M_CGA_array)  # The M in CGA multivector form - array

    print("M in PGA multivector form:")
    M_PGA_array = matrix_to_motor(M, method='PGA').value
    print(M_PGA_array)  # The M in PGA multivector form - array

    print("Traditional Representation forms:")
    extracted_theta, extracted_axis, extracted_translation_vector = matrix_to_angle_axis_translation(
        M)  # notice theta is in rad
    q = Quaternion.from_angle_axis(angle=extracted_theta, axis=extracted_axis)
    print("extracted theta: ", extracted_theta, "\t VS original :", np.radians(theta))
    print("extracted axis: ", extracted_axis, "\t VS original :", axis / np.linalg.norm(axis))
    print("extracted translation_vector", extracted_translation_vector, "\t VS original :", translation_vector)
    print("extracted quaternion: ", q)

    # v_pga = matrix_to_motor(M, method = 'PGA').value

    print("=" * 20)
    print("OBTAIN THE TR MATRIX FROM ITS VARIOUS FORMS")
    print("=" * 20)

    print("From flatten form")
    print(M_flatten.reshape(4, 4))

    print("From CGA array")
    layout_orig, _ = cl.Cl(3)
    layout_CGA, _, _ = cl.conformalize(layout_orig)
    m = cl.MultiVector(layout=layout_CGA, value=M_CGA_array)
    t, q = extract_t_q_from_TR(m, algebra='CGA')
    print(matrix_from_t_and_q(t, q))

    print("From PGA array")
    layout_PGA, _ = cl.Cl(3, 0, 1, firstIdx=0)
    m = cl.MultiVector(layout=layout_PGA, value=M_PGA_array)
    t, q = extract_t_q_from_TR(m, algebra='PGA')
    print(matrix_from_t_and_q(t, q))

    print("From theta, axis, angle")
    t = extracted_translation_vector
    q = Quaternion.from_angle_axis(angle=extracted_theta, axis=extracted_axis)
    q = [q.x, q.y, q.z, q.w]  # in list form
    print(matrix_from_t_and_q(t, q))

    # PGA TESTS
    print("=" * 20)
    print("PGA TESTS")
    print("=" * 20)
    T = 1 - 0.5 * pga.e0 * (6 * pga.e1 + 7 * pga.e2 + 8 * pga.e3)
    R = 1 + 2 * pga.e12 + 3 * pga.e13 + 4 * pga.e23
    TR = T * R

    extractedT, extractedR = extract_T_R_from_TR_PGA(TR)
    print("T: ", T)
    print("R: ", R)
    print("extractedT ", extractedT)
    print("extractedR ", extractedR)

    # CGA TESTS
    print("=" * 20)
    print("CGA TESTS")
    print("=" * 20)
    t = [1, 2, 3]
    q = [1, 2, 3, 4]  # x,y,z,w
    TR = t_q_to_TR(t, q)

    print(TR.value)
    t1, q1 = extract_t_q_from_TR(TR, algebra='CGA')
    print("t = ", t1)
    print("q = ", q1)
