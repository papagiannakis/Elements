from clifford.g3c import *
from clifford import Cl, conformalize


G3, blades_g3 = Cl(3)
G3c, blades_g3c, stuff = conformalize(G3)


def t_q_to_TR(t,q):
  """
  Takes in a quaternion (q) and translation vector (t) and generates the respective CGA motor (TR)
  """
  T = 1 - 0.5*(t[0]*e1+t[1]*e2+t[2]*e3)*einf
  R = q[3] - q[2]*e12 + q[1]*e13 - q[0]*e23
  # print("T = ", T)
  # print("R = ", R)
  return T*R

def extract_t_q_from_TR(TR):
  """
  Takes in a TR CGA motor and extracts the quaternion (q) and translation vector (t)
  """
  no = -eo
  R = TR(e123)
  T = (TR*~R).normal()
  # print("T = ", T)
  # print("R = ", R)
  tt = -2*(T|no) 
  t = [tt[e1],tt[e2],tt[e3]]
  q = [-R[e23],R[e13],-R[e12],R.value[0]] 
  return t, q



if __name__ == "__main__":

    t = [1,2,3]
    q = [1,2,3,4] # x,y,z,w
    TR = t_q_to_TR(t,q)

    t1,q1 = extract_t_q_from_TR(TR)
    print("t = ", t1)
    print("q = ", q1)

