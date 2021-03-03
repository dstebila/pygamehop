import unittest
import gamehop
import gamehop.inlining
import gamehop.verification

def h():        
    return 1

def f_target():
    r = 1
    return r

class TestReturnConstant(unittest.TestCase):
    def test_sometest(self):
        s1 = gamehop.verification.canonicalize_function(f_target)
        s2 = gamehop.verification.canonicalize_function(h)
        self.assertEqual(s1, s2)
