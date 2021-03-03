import unittest
import gamehop
import gamehop.inlining
import gamehop.verification

def h(x): return None
def g(x,y,z): return None
def E(x,y): return None

def f(pke):
    m0 = h(pke.MS)
    m1 = h(pke.MS)    
    ct = E(m0)
    r = g(ct, m1)
    return r

def f_target(pke):
    m0 = h(pke.MS)
    ct = E(m0)
    m1 = h(pke.MS)
    r = g(ct, m1)
    return r



class TestLineOrderingCommutes(unittest.TestCase):
   def test_sometest(self):
      s1 = gamehop.verification.canonicalize_function(f_target)
      s2 = gamehop.verification.canonicalize_function(f)
      print(s1)
      print(s2)
      self.assertEqual(s1, s2)
