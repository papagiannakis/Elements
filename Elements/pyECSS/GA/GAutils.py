import clifford.g3c as cga
import clifford.pga as pga

import numpy as np

import Elements.pyECSS.utilities as util


###### CGA START ######

def t_q_to_TR(t,q):
  """
  Takes in a quaternion (q) and translation vector (t) and generates the respective CGA motor (TR)
  """
  T = 1 - 0.5*(t[0]*cga.e1+t[1]*cga.e2+t[2]*cga.e3)*cga.einf
  R = q[3] - q[2]*cga.e12 + q[1]*cga.e13 - q[0]*cga.e23
  # print("T = ", T)
  # print("R = ", R)
  return T*R

def extract_t_q_from_TR(TR, algebra = 'CGA'):
   if algebra == 'CGA':
      return extract_t_q_from_TR_CGA(TR)
   else:
      pass

def extract_t_q_from_TR_CGA(TR):
  """
  Takes in a TR CGA motor and extracts the quaternion (q) and translation vector (t)
  """
  no = -cga.eo
  R = TR(cga.e123)
  T = (TR*~R).normal()
  # print("T = ", T)
  # print("R = ", R)
  tt = -2*(T|no) 
  t = [tt[cga.e1],tt[cga.e2],tt[cga.e3]]
  q = [-R[cga.e23],R[cga.e13],-R[cga.e12],R.value[0]] 
  return t, q


# e23, no, e123

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
    axis[0] = matrix[2,1] - matrix[1,2]
    axis[1] = matrix[0,2] - matrix[2,0]
    axis[2] = matrix[1,0] - matrix[0,1]

    # Angle.
    r = np.hypot(axis[0], np.hypot(axis[1], axis[2]))
    t = matrix[0,0] + matrix[1,1] + matrix[2,2]
    theta = np.arctan2(r, t-1)
    # np.atan2
    # Normalise the axis.
    axis = axis / r

    # Return the data.
    if abs(theta) < 1e-6 :
        axis = [1,0,0]
    
    return theta, axis, matrix[0:3,3]

def matrix_to_motor(M, method = 'CGA'):
    "The matrix has to represent rotation and translation only, no scaling of x,y or z."
    if method == 'PGA':
      T,R = matrix_to_t_r_pga(M)
    else:
      T,R = matrix_to_t_r_cga(M)
    return T*R

def matrix_to_t_r_cga(M):
    "The matrix has to represent rotation and translation only, no scaling of x,y or z."
    phi,axis,trans = matrix_to_angle_axis_translation(M)
    if phi == 0 or np.isnan(axis[0]) or np.isnan(axis[1]) or np.isnan(axis[2]): 
        R = 1
    else:
        # axis from euc to cga and normalization
        axis_cga = axis[0]*cga.e1+axis[1]*cga.e2+axis[2]*cga.e3
        axis_cga = axis_cga/ np.linalg.norm(axis)
        I3_cga = cga.e1*cga.e2*cga.e3 
        R = np.e**(-(axis_cga*I3_cga)*(phi/2))   # rotor

    # update trans from euclidean vector to  cga
    t = trans[0]*cga.e1+trans[1]*cga.e2+trans[2]*cga.e3
    T = np.e**(-1/2*t*cga.einf)          # translator
    return T,R

###### CGA END ######

# PGA below


def rotor_from_axis_angle_pga(axis,angle):
    "returns the pga multivector rotor that corresponds to rotation around axis=[x,y,z] by angle (in rads)"
    axis_pga = axis[0]*pga.e1+axis[1]*pga.e2+axis[2]*pga.e3
    u = axis_pga/np.linalg.norm(axis)
    I3_pga = pga.e1*pga.e2*pga.e3
    return np.cos(angle/2)-u*I3_pga*np.sin(angle/2)
#     return np.e**(-(u*I3_pga)*(angle/2))


def matrix_to_t_r_pga(M):
    "The matrix has to represent rotation and translation only, no scaling of x,y or z."
    angle,axis,trans = matrix_to_angle_axis_translation(M)
    if angle == 0 or np.isnan(axis[0]) or np.isnan(axis[1]) or np.isnan(axis[2]): 
        R = 1
    else:
        R = rotor_from_axis_angle_pga(axis,angle)
    T = 1-1/2*pga.e0*(trans[0]*pga.e1+trans[1]*pga.e2+trans[2]*pga.e3) #T = translator(trans)
    return T,R


if __name__ == "__main__":

    t = [1,2,3]
    q = [1,2,3,4] # x,y,z,w
    TR = t_q_to_TR(t,q)

    print (TR.value)
    t1,q1 = extract_t_q_from_TR_CGA(TR)
    print("t = ", t1)
    print("q = ", q1)

    M = util.translate([1,2,3])@util.rotate(axis=[1,2,3], angle=30)
    print (matrix_to_angle_axis_translation(M))
    print([1,2,3]/np.linalg.norm([1,2,3]))
    print(2*np.pi*30/360)

    print (matrix_to_motor(M, method = 'CGA').value)
    print (matrix_to_motor(M, method = 'PGA').value)


    
