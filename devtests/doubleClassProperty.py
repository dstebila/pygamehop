import unittest
import gamehop
import gamehop.inlining
import gamehop.verification

class g: 
   x : 1

def j(x):
   return j
def h(x):     
   y = j(g.x)
   z = j(g.x)
   return y + z

def f_target(x):   
   v = g.x
   y = j(v)
   z = j(v)   
   r = y + z
   return r

class TestDoubleClassProperty(unittest.TestCase):
   def test_sometest(self):
      s1 = gamehop.verification.canonicalize_function(f_target)
      s2 = gamehop.verification.canonicalize_function(h)
      print(s1)
      print(s2)
      self.assertEqual(s1, s2)
