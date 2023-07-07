"""
Unit tests
Employing the unittest standard python test framework
https://docs.python.org/3/library/unittest.html
    
Elements.pyECSS (Entity Component Systems in a Scenegraph) package
@Copyright 2021-2022 Dr. George Papagiannakis

"""

import unittest
import numpy as np
from scipy.spatial.transform import Rotation as R
from scipy.spatial.transform import Slerp

from Elements.pyECSS.math_utilities import *

class TestUtilities(unittest.TestCase):
    """ main class to test CG utilities and convenience functions """
    
    def test_vec(self):
        """
        test_vec function
        """
        print("\nTestUtilities:test_vec() START")
        a = [1.0,0.0,0.0,1.0]
        vec_a = vec(a)  
        np_a = np.array([1.0,0.0,0.0,1.0],dtype=np.float,order='F')
        
        self.assertEqual(vec_a.tolist(), np_a.tolist())
        np.testing.assert_array_equal(vec_a,np_a)
        print(vec_a)
        print(np_a)
    
        print("TestUtilities:test_vec() END")
    
    def test_normalised(self):
        """
        test_normalised function
        """
        print("\nTestUtilities:test_normalised() START")
        a = [2.0,2.0,0.0,1.0]
        vec_a = vec(a)  
        norm_vec = normalise(vec_a)
        norm_a = normalise(a) # in this case the simple list will be converted to numpy array first implicitly
        np_a = np.array([2.0,2.0,0.0,1.0],dtype=np.float,order='F')
        norm_np = np.array([0.666667,0.666667,0.0,0.333333],dtype=np.float,order='F')
        
        self.assertAlmostEqual(norm_vec.all(), norm_np.all())
        self.assertAlmostEqual(norm_a.all(), norm_np.all())
        np.testing.assert_array_almost_equal(norm_vec,norm_np,decimal=5)
        np.testing.assert_array_almost_equal(norm_a,norm_np,decimal=5)
        print(norm_vec)
        print(norm_np)
        print(norm_a)
    
        print("TestUtilities:test_normalised() END")
    
    def test_lerp(self):
        """Test linear interpolation between two points"""
        print("\nTestUtilities:test_lerp() START")
        
        # lerp between 0.0 to 1.0
        point0 = lerp(0.0, 1.0, 0.0)
        point1 = lerp(0.0, 1.0, 1.0)
        pointb = lerp(0.0, 1.0, 0.5)
        print(point0)
        print(point1)
        print(pointb)
        
        self.assertEqual(point0, 0)
        self.assertEqual(point1, 1)
        self.assertEqual(pointb, 0.5)
        
        print("\TestUtilities:test_lerp() END")
        
    def test_identity(self):
        """
        test_identity function
        """
        print("\nTestUtilities:test_identity() START")
        matI = identity(4)
        np_i1 = np.ones((4,4))
        np_i4 = np.identity(4)
        np_i = np.array([
            [1.0,0.0,0.0,0.0],
            [0.0,1.0,0.0,0.0],
            [0.0,0.0,1.0,0.0],
            [0.0,0.0,0.0,1.0],
        ],dtype=np.float,order='F')
        
        self.assertEqual(matI.tolist(), np_i4.tolist())
        self.assertEqual(matI.tolist(), np_i.tolist())
        self.assertNotEqual(matI.tolist(), np_i1.tolist())
        print(matI)
        print(np_i)
        print(np_i1)
    
        print("TestUtilities:test_identity() END")
        
    def test_inverse(self):
        """
        test_inverse function, 
        https://numpy.org/doc/stable/reference/generated/numpy.linalg.inv.html
        """
        print("\nTestUtilities:test_rotate() START")
        
        mLat = np.array([
            [1,0,0,1],
            [0,1,0,2],
            [0,0,1,3],
            [0,0,0,1]
        ],dtype=np.float,order='F') 
        
        mLatInv = np.array([
            [1,0,0,-1],
            [0,1,0,-2],
            [0,0,1,-3],
            [0,0,0,1]
        ],dtype=np.float,order='F') 
        
        utilmLatInv = inverse(mLat)
        np.testing.assert_array_almost_equal(utilmLatInv,mLatInv,decimal=5)
       
        print(utilmLatInv)
        print(mLatInv)

    
        print("TestUtilities:test_inverse() END")
    
    def test_ortho(self):
        """
        test_ortho function, 
        tested against results from https://glm.g-truc.net/0.9.2/api/a00245.html
        """
        print("\nTestUtilities:test_ortho() START")
        matOrtho = ortho(-100.0, 100.0, -100.0, 100.0, 1.0, 100.0)
        np_Ortho = np.array([
            [0.01,0.0,0.0,0.0],
            [0.0,0.01,0.0,0.0],
            [0.0,0.0,-0.020202,-1.0202],
            [0.0,0.0,0.0,1.0],
        ],dtype=np.float,order='F')
        
        self.assertAlmostEqual(matOrtho.all(), np_Ortho.all())
       
        print(matOrtho)
        print(np_Ortho)
    
        print("TestUtilities:test_ortho() END")
        
    def test_perspective(self):
        """
        test_perspective function, 
        tested against results from https://glm.g-truc.net/0.9.2/api/a00245.html
        """
        print("\nTestUtilities:test_perspective() START")
        matPersp = perspective(90.0, 1, 0.1, 100)
        np_Persp = np.array([
            [1.0,0.0,0.0,0.0],
            [0.0,1.0,0.0,0.0],
            [0.0,0.0,-1.002,-0.2002],
            [0.0,0.0,-1.0,0.0],
        ],dtype=np.float,order='F')
        
        matPersp2 = perspective(45.0, 1.33, 0.1, 100)
        np_Persp2 = np.array([
            [1.815,0.0,0.0,0.0],
            [0.0,2.414,0.0,0.0],
            [0.0,0.0,-1.002,-0.2002],
            [0.0,0.0,-1.0,0.0],
        ],dtype=np.float,order='F')
        
        #self.assertAlmostEqual(matPersp.all(), np_Persp.all())
        np.testing.assert_array_almost_equal(matPersp,np_Persp,decimal=5)
        np.testing.assert_array_almost_equal(matPersp2,np_Persp2,decimal=3)
        
        print(matPersp)
        print(np_Persp)
    
        print("TestUtilities:test_perspective() END")
        
    def test_frustum(self):
        """
        test_frustum function, 
        tested against results from https://glm.g-truc.net/0.9.2/api/a00245.html
        """
        print("\nTestUtilities:test_frustum() START")
        matPersp = frustum(-10.0, 10.0,-10.0,10.0, 0.1, 100)
        np_Persp = np.array([
            [0.01,0.0,0.0,0.0],
            [0.0,0.01,0.0,0.0],
            [0.0,0.0,-1.002,-0.2002],
            [0.0,0.0,-1.0,0.0],
        ],dtype=np.float,order='F')
        
        self.assertAlmostEqual(matPersp.all(), np_Persp.all())
       
        print(matPersp)
        print(np_Persp)
    
        print("TestUtilities:test_frustum() END")
    
    def test_translate(self):
        """
        test_translate function, 
        tested against results from https://glm.g-truc.net/0.9.2/api/a00245.html
        """
        print("\nTestUtilities:test_translate() START")
        matTrans = translate(1.0, 2.0, 3.0)
        matTrans2 = translate(vec(1.0, 2.0, 3.0))
        mT = np.array([
            [1.0,0.0,0.0,1.0],
            [0.0,1.0,0.0,2.0],
            [0.0,0.0,1.0,3.0],
            [0.0,0.0,0.0,1.0],
        ],dtype=np.float,order='F')
        
        self.assertEqual(matTrans.tolist(), mT.tolist())
        self.assertEqual(matTrans2.tolist(), mT.tolist())
        np.testing.assert_array_equal(matTrans,mT)
        np.testing.assert_array_equal(matTrans2,mT)
       
        print(matTrans)
        print(matTrans2)
        print(mT)
    
        print("TestUtilities:test_translate() END")
        
    
    def test_scale(self):
        """
        test_scale function, 
        tested against results from https://glm.g-truc.net/0.9.2/api/a00245.html
        """
        print("\nTestUtilities:test_scale() START")
        matTrans = scale(1.0, 2.0, 3.0)
        matTrans2 = scale(vec(1.0, 2.0, 3.0))
        matTrans3 = scale(10.0) #uniform scaling
        mT = np.array([
            [1.0,0.0,0.0,0.0],
            [0.0,2.0,0.0,0.0],
            [0.0,0.0,3.0,0.0],
            [0.0,0.0,0.0,1.0],
        ],dtype=np.float,order='F')
        mT3 = np.array([
            [10.0,0.0,0.0,0.0],
            [0.0,10.0,0.0,0.0],
            [0.0,0.0,10.0,0.0],
            [0.0,0.0,0.0,1.0],
        ],dtype=np.float,order='F')
        
        self.assertEqual(matTrans.tolist(), mT.tolist())
        self.assertEqual(matTrans2.tolist(), mT.tolist())
        self.assertEqual(matTrans3.tolist(), mT3.tolist())
       
        print(matTrans)
        print(matTrans2)
        print(mT)
        print(matTrans3)
    
        print("TestUtilities:test_scale() END")
        
    def test_sincos(self):
        """
        test_sincos is sine cosine calculation function, 
        tested against results from https://glm.g-truc.net/0.9.4/api/a00136.html
        from GLM 0.9.5.1 radians are default and not degrees: GLM_FORCE_RADIANS 
        """
        print("\nTestUtilities:test_sincos() START")
        
        cos0 = 1.0
        cos45 = 0.7071067811865476
        sin0 = 0.0
        sin90 = 1.0
        cos90 = 0.0
        
        sine0, cosine0 = sincos(0.0)
        sine45, cosine45 = sincos(45, np.pi/4)
        sine90, cosine90 = sincos(90, np.pi/2)
        sine90d, cosine90d = sincos(90) #cosine90 does not return pure 0
        
        print(f' sine90: {sine90}, sin90: {sin90}')
        print(f' cosine90: {cosine90}, cos90: {cos90}')
        print(f' cosine90d: {cosine90d}, sine90d: {sine90d}')
        print(f' sine0: {sine90}, sin0: {sin0}')
        print(f' cosine0: {cosine0}, cos0: {cos0}')
        print(f' cosine45: {cosine45}, cos45: {cos45}')
        
        self.assertAlmostEqual(sine0, sin0)
        self.assertAlmostEqual(sine90, sin90)
        self.assertAlmostEqual(sine90d, sin90)
        self.assertAlmostEqual(cosine0, cos0)
        self.assertAlmostEqual(cosine90, cos90)
        self.assertAlmostEqual(cosine90d, cos90)
        self.assertAlmostEqual(cosine45, cos45)
        self.assertAlmostEqual(sine45, cos45)
        
        print("TestUtilities:test_sincos() END")    
    
        
    def test_rotate(self):
        """
        test_rotate function, 
        tested against results from https://glm.g-truc.net/0.9.2/api/a00245.html
        and theory: https://en.wikipedia.org/wiki/Rotation_matrix 
        """
        print("\nTestUtilities:test_rotate() START")
        axis=(1.0, 1.0, 1.0)
        angle = 90.0
        matRot = rotate(axis, angle)
        
        mR = np.array([
            [0.333333,-0.244017,0.910684,0.0],
            [0.910684,0.333333,-0.244017,0.0],
            [-0.244017,0.910684,0.333333,0.0],
            [0.0,0.0,0.0,1.0],
        ],dtype=np.float,order='F')
        
        #self.assertAlmostEquals(matRot.all(), mR.all(),6)
        np.testing.assert_array_almost_equal(matRot,mR,decimal=6)
        np.testing.assert_array_almost_equal(matRot,mR)
       
       
        print(matRot)
        print(mR)
    
        print("TestUtilities:test_rotate() END")
    
    
    def test_lookat(self):
        """
        test_lookat function, 
        tested against results from 
        https://github.com/g-truc/glm/blob/master/glm/ext/matrix_transform.inl
        and https://github.com/Zuzu-Typ/PyGLM/blob/master/wiki/function-reference/stable_extensions/matrix_transform.md#lookAt-function 
        """
        print("\nTestUtilities:test_rotate() START")
        eye = (1.0, 1.0, 1.0)
        target = (10,10,10)
        up = (0.0, 1.0, 0.0)
        matLookat = lookat(eye, target, up)               
        mLat = np.array([[ -0.707107,   0.0,       0.707107,  -0.0       ],
                         [-0.408248,   0.816497,  -0.408248,  -0.0       ],
                         [ -0.57735,    -0.57735,   -0.577353,  1.73205081],
                         [ 0.0,        0.0,        0.0,        1.0       ]],
                         dtype=np.float,order='F') #glm.lookAtRH

        ## 
        matLookat2 = lookat((0.0, 0.0, -1.0), (0.0, 0.0, 0.0), (0.0, 1.0, 0.0))
        mLat2 = np.array([
            [-1.0,0.0,0.0,-0.0],
            [0.0,1.0,0.0,-0.0],
            [0.0,0.0,-1.0,-1.0],
            [0.0,0.0,0.0,1.0]],
            dtype=np.float,order='F') #glm.lookAtRH
        
        ##
        matLookat3 = lookat((1.0, 2.0, 3.0), (3.0, 2.0, 1.0), (0.0, 1.0, 0.0))
        mLat3 = np.array([[0.70710678,  0.0,         0.70710678,  -2.82842712 ],
                          [ 0.0,         1.0,          0.0,         -2.        ],
                          [ -0.70710678,  0.0,         0.70710678,  -1.41421356 ],
                          [ 0.0,         0.0,          0.0,          1.        ]],
                          dtype=np.float,order='F')
        
        
       

        np.testing.assert_array_almost_equal(matLookat,mLat,decimal=5)
        np.testing.assert_array_almost_equal(matLookat2,mLat2,decimal=5)
        np.testing.assert_array_almost_equal(matLookat3,mLat3,decimal=5)
    
        print("TestUtilities:test_lookat() END")
        
    
    def test_quaternion(self):
        """
        test_quaternion to test quaternion algebra elements from individual components or vec4
        tested against scipy.spatial.transform.Rotation (by default produces normalised quaternions)
        and glm.quat: NOTE GLM IS SCALAR-FIRST 
        """
        print("\nTestUtilities:test_quaternion() START")
        
        quat_a = quaternion(1.0,1.0,1.0,1.0)
        vec_a = vec(1.0, 1.0, 1.0)  
        quat_a_vec = quaternion(vec_a, 1.0)
        quat_a_vec_norm = normalise(quat_a_vec)
        
        quat_np_a = np.array([1.0,1.0,1.0,1.0],dtype=np.float,order='F')
        rot = R.from_quat(quat_np_a)
        
        quat_b = quaternion(1.0,2.0,3.0,4.0)
        quat_b = normalise(quat_b)
        rot_b = R.from_quat([1.0, 2.0, 3.0, 4.0])
        
        rot_c = R.from_rotvec(np.pi/2 * np.array([0, 0, 1]))
        quat_c = quaternion_from_axis_angle([0.0,0.0,1.0],90.0)
        
        rot_euler = R.from_euler('y', [90], degrees=True)
        quat_euler = quaternion_from_euler(0.0,90.0,0.0)
        
        rot_ab = rot * rot_b; #somehow this scipy quat mult yields different results than ours or glm!!!
        rot_ab_glm = R.from_quat( [0.365148, 0.182574,0.547723, -0.730297])
        quat_ab = quaternion_mul(quat_a_vec_norm, quat_b)
        
        quat_ab_matrix = quaternion_matrix(quat_ab)
        
        quat_slerp = quaternion_slerp(quat_a_vec_norm, quat_b, 0.5)
        rot_ab_glm_slerp = R.from_quat( [0.348973, 0.442316, 0.535659,  0.629002])
        """key_rots = np.array([rot, rot_b])
        key_times = [0, 1]
        slerp = Slerp(key_times,key_rots)
        rot_ab_slerp = slerp([0.5])
        """
        
        print("\nquat_a:\t", quat_a)
        print("quat_a_vec:\t", quat_a_vec)
        print("rot.as_quat():\t", rot.as_quat())
        print("quat_a_vec_norm:\t",quat_a_vec_norm)
        print("\nrot_b.as_quat():\t", rot_b.as_quat())
        print("quat_b:\t", quat_b)
        print("\nrot_c.as_quat():\t ", rot_c.as_quat())
        print("quat_c:\t ", quat_c)
        print("\nrot_euler.as_quat():\t ", rot_euler.as_quat())
        print("quat_euler:\t ", quat_euler)
        print("\nrot_ab_glm.as_quat():\t ", rot_ab_glm.as_quat())
        print("quat_ab:\t ", quat_ab)
        print("rot_ab.as_quat():\t ", rot_ab.as_quat())
        print("\nquat_ab_matrix: ",quat_ab_matrix)
        print("rot_ab_glm.as_matrix(): ",rot_ab_glm.as_matrix())
        print("\nquat_slerp: ",normalise(quat_slerp))
        print("rot_ab_glm_slerp: ",rot_ab_glm_slerp.as_quat())
        #print("rot_ab_slerp: ",rot_ab_slerp.as_quat()) #quat slerp is untested as it gives different results than glm!

        np.testing.assert_array_almost_equal(quat_a,quat_np_a)
        np.testing.assert_array_almost_equal(quat_a,quat_a_vec)
        np.testing.assert_array_almost_equal(rot.as_quat(),quat_a_vec_norm)
        np.testing.assert_array_almost_equal(rot_b.as_quat(),quat_b)
        np.testing.assert_array_almost_equal(rot_c.as_quat(),quat_c)
        np.testing.assert_array_almost_equal(rot_ab_glm.as_quat(),quat_ab)
        np.testing.assert_array_almost_equal(rot_ab_glm_slerp.as_quat(),quat_slerp)
    
        print("TestUtilities:test_quaternion() END")
        

if __name__ == "__main__":
    unittest.main(argv=[''], verbosity=3, exit=False)