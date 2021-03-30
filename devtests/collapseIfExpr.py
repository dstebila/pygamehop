import unittest
import gamehop
import gamehop.inlining
import gamehop.verification

def f_first(x, y):
    z = x if 0 == 0 else y
    return z
def f_first_target(x, y):
    return x

def f_second(x, y):
    z = x if 0 == 1 else y
    return z
def f_second_target(x, y):
    return x


class TestCollapseIfExpr(unittest.TestCase):
   def test_first(self):
      s1 = gamehop.verification.canonicalize_function(f_first)
      s2 = gamehop.verification.canonicalize_function(f_first_target)
      print(s1)
      print(s2)
      self.assertEqual(s1, s2)
   def test_second(self):
      s1 = gamehop.verification.canonicalize_function(f_second)
      s2 = gamehop.verification.canonicalize_function(f_second_target)
      print(s1)
      print(s2)
      self.assertEqual(s1, s2)
