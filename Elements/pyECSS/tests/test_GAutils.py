import Elements.pyECSS.GA.GAutils as GAutil
import clifford.g3c as cga
import clifford.pga as pga
import Elements.pyECSS.utilities as util  
from Elements.pyECSS.GA.quaternion import Quaternion
import unittest
import numpy as np

# create unittest for GAutils.py
class TestGAutils(unittest.TestCase):
    
    def setUp(self):
        self.theta = 30 # in degrees
        self.axis = [1,2,3] # axis of rotation
        self.translation_vector = [1,2,3] # translation vector
        self.M = util.translate(self.translation_vector)@util.rotate(axis=self.axis, angle=self.theta)
        print("Original M:\n", self.M)

    def test_setup_of_M(self):
        # self.M_flatten = self.M.flatten()
        self.expected_M = np.array([ 
            [0.87559503, -0.3817526, 0.29597008,  1], 
            [0.42003107, 0.90430385, -0.07621294, 2],  
            [-0.23855239,  0.1910483, 0.9521519,  3],
            [0,   0,   0,   1 ] ])
        np.testing.assert_array_almost_equal(self.M, self.expected_M, decimal = 6)

    def test_quaternion_and_matrix_from_t_and_q(self):
        q = Quaternion.from_angle_axis(angle = np.radians(self.theta), axis = self.axis)
        q = [q.x, q.y, q.z, q.w] # in list form
        np.testing.assert_array_almost_equal(np.array(q), np.array([0.06917229585140207, 0.13834459170280414, 0.2075168798407978, 0.9659258315286792]))
        
        np.testing.assert_array_almost_equal(GAutil.matrix_from_t_and_q(self.translation_vector, q), self.M, decimal = 6)

    def test_angle_axis_translation_extraction(self):
        
        extracted_theta, extracted_axis, extracted_translation_vector = GAutil.matrix_to_angle_axis_translation(self.M) # notice theta is in rad
        extracted_quaternion = Quaternion.from_angle_axis(angle = extracted_theta, axis = extracted_axis)
        
        np.testing.assert_array_almost_equal(extracted_theta, np.radians(self.theta), decimal = 6)
        np.testing.assert_array_almost_equal(extracted_axis, self.axis/np.linalg.norm(self.axis), decimal = 6)  
        
        np.testing.assert_array_almost_equal(extracted_translation_vector, self.translation_vector, decimal = 6)    
        np.testing.assert_array_almost_equal(extracted_translation_vector, self.M[:3,3], decimal = 6)

        np.testing.assert_array_almost_equal(extracted_quaternion.to_rotation_matrix(), self.M[:3,:3], decimal = 6)


        t = extracted_translation_vector
        q = extracted_quaternion
        q = [q.x, q.y, q.z, q.w] # in list form
        print("q", q)
        np.testing.assert_array_almost_equal(GAutil.matrix_from_t_and_q(t,q), self.M, decimal = 6)

    def test_matrix_to_motor_PGA(self):
        actual_outpout = GAutil.matrix_to_motor(self.M, method = 'PGA').value
        expected_output = np.array([ 0.96592583, 0, 0, 0, 0, -0.48296291 ,-0.96592584 ,-1.44888875 ,-0.20751688, 0.13834459, -0.0691723, 0, 0, 0, 0, 0.48420606])
        np.testing.assert_array_almost_equal(actual_outpout, expected_output, decimal = 6)

    def test_matrix_to_motor_CGA(self):
        actual_outpout = GAutil.matrix_to_motor(self.M, method = 'CGA').value
        # print("actual_outpout", actual_outpout)
        expected_output = np.array([ 0.96592583, 0,0,0,0,0, -0.20751688, 0.13834459, -0.48296291, -0.48296291, -0.0691723,-0.96592584,-0.96592584,-1.44888875,-1.44888875,0,0,0,0,0,0,0,0,0,0,0,0.48420606, 0.48420606,0,0,0,0])
        np.testing.assert_array_almost_equal(actual_outpout, expected_output, decimal = 6)
     
    def test_flatten_and_back(self):
        self.M_flatten = self.M.flatten()
        self.M_back = self.M_flatten.reshape(4,4)
        np.testing.assert_array_almost_equal(self.M_back, self.M, decimal = 6)

    def test_PGA_vec_to_matrix(self):
        self.PGA_vec = GAutil.matrix_to_motor(self.M, method = 'PGA').value
        self.M_back = GAutil.PGA_vec_to_TRS_matrix(self.PGA_vec)
        # print("M_back", self.M_back)
        np.testing.assert_array_almost_equal(self.M_back, self.M, decimal = 6)

    def test_CGA_vec_to_matrix(self):
        self.CGA_vec = GAutil.matrix_to_motor(self.M, method = 'CGA').value
        self.M_back = GAutil.CGA_vec_to_TRS_matrix(self.CGA_vec)
        # print("M_back", self.M_back)
        np.testing.assert_array_almost_equal(self.M_back, self.M, decimal = 6)

    def test_various_PGA(self):
        #     # PGA TESTS
        T = 1 - 0.5*pga.e0*(6*pga.e1 + 7*pga.e2 + 8*pga.e3)
        R = 1 +2*pga.e12 + 3*pga.e13 +4*pga.e23
        TR = T*R

        extractedT, extractedR =  GAutil.extract_T_R_from_TR_PGA(TR)
        np.testing.assert_array_almost_equal(extractedT.value, T.value, decimal = 6)
        np.testing.assert_array_almost_equal(extractedR.value, R.value, decimal = 6)

    def test_various_CGA(self):

        t = [1,2,3]
        q = [1,2,3,4] # x,y,z,w
        
        TR = GAutil.t_q_to_TR(t,q) # CGA vector from t and q
        expected_result = np.array([ 4,0,0,0,0,0,-3,2,-2,-2,-1,-4,-4,-6,-6,0,0,0,0,0,0,0,0,0,0,0,7,7,0,0,0,0.])
        np.testing.assert_array_almost_equal(TR.value, expected_result, decimal = 6)
        
        t1,q1 = GAutil.extract_t_q_from_TR(TR, algebra = 'CGA')
        np.testing.assert_array_almost_equal(t, t1, decimal = 6)
        np.testing.assert_array_almost_equal(q, q1, decimal = 6)
        

    # print("Traditional Representation forms:")
#     extracted_theta, extracted_axis, extracted_translation_vector = matrix_to_angle_axis_translation(M) # notice theta is in rad
#     q = Quaternion.from_angle_axis(angle = extracted_theta, axis = extracted_axis)
#     print("extracted theta: ", extracted_theta, "\t VS original :", np.radians(theta))
#     print("extracted axis: ", extracted_axis, "\t VS original :", axis/np.linalg.norm(axis))
#     print("extracted translation_vector", extracted_translation_vector, "\t VS original :", translation_vector)
#     print("extracted quaternion: ", q)
    #     print("Traditional Representation forms:")
#     extracted_theta, extracted_axis, extracted_translation_vector = matrix_to_angle_axis_translation(M) # notice theta is in rad
#     q = Quaternion.from_angle_axis(angle = extracted_theta, axis = extracted_axis)
#     print("extracted theta: ", extracted_theta, "\t VS original :", np.radians(theta))
#     print("extracted axis: ", extracted_axis, "\t VS original :", axis/np.linalg.norm(axis))
#     print("extracted translation_vector", extracted_translation_vector, "\t VS original :", translation_vector)
#     print("extracted quaternion: ", q)
    
    # create test for t_q_to_TR
    # def test_t_q_to_TR(self):
    #     # create test cases
    #     t = [1,2,3]
    #     q = [4,5,6,7]
    #     # create expected output
    #     expected_output = 1
    #     # create actual output
    #     actual_output = t_q_to_TR(t,q)
    #     # compare actual output to expected output
    #     self.assertEqual(actual_output, expected_output)


# if __name__ == '__main__':

 
    

#     # PGA TESTS
#     print("="*20)
#     print("PGA TESTS")
#     print("="*20)
#     T = 1 - 0.5*pga.e0*(6*pga.e1 + 7*pga.e2 + 8*pga.e3)
#     R = 1 +2*pga.e12 + 3*pga.e13 +4*pga.e23
#     TR = T*R

#     extractedT, extractedR =  extract_T_R_from_TR_PGA(TR)
#     print("T: ", T)
#     print("R: ", R)
#     print("extractedT ", extractedT)
#     print("extractedR ", extractedR)

#     # CGA TESTS
#     print("="*20)
#     print("CGA TESTS")
#     print("="*20)
#     t = [1,2,3]
#     q = [1,2,3,4] # x,y,z,w
#     TR = t_q_to_TR(t,q)

#     print (TR.value)
#     t1,q1 = extract_t_q_from_TR(TR, algebra = 'CGA')
#     print("t = ", t1)
#     print("q = ", q1)

