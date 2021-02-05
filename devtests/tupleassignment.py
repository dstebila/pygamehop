import unittest
import gamehop.inlining
import gamehop.verification

def h():
    c = 1
    d = 2
    (a,b) = (c,d)
    return a

def f_target():
    return 1


s1 = gamehop.verification.canonicalize_function(h)
s2 = gamehop.verification.canonicalize_function(f_target)


class TestClassInlineProp(unittest.TestCase):
    def test_sometest(self):
        self.assertEqual(s1, s2)

if True:
    print(s1)
    print(test1)
    print(s2)
    print("---------------Diff-----------------")
    gamehop.verification.stringDiff(s1, s2)
    print("------------------------------------")
