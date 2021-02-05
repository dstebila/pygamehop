import unittest
import gamehop.inlining
import gamehop.verification

def h(x: int, y: int):
    r = x + 2 * y
    return r

def f_target(y: int, x: int):
    r = x + 2 * y
    return r


s1 = gamehop.verification.canonicalize_function(f_target)
s2 = gamehop.verification.canonicalize_function(h)


class TestClassInlineProp(unittest.TestCase):
    def test_sometest(self):
        self.assertEqual(s1, s2)

if True:
    print(s1)
    print(s2)
    print("---------------Diff-----------------")
    gamehop.verification.stringDiff(s1, s2)
    print("------------------------------------")
