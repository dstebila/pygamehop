import unittest
import gamehop
import gamehop.inlining
import gamehop.verification



def h(a,b):
    c = (a,b)
    (x,y) = c
    return x + y

def f_target(a,b):    
    return a + b


s1 = gamehop.verification.canonicalize_function(h)
s2 = gamehop.verification.canonicalize_function(f_target)


class TestTupleCollapse(unittest.TestCase):
    def test_sometest(self):
        self.assertEqual(s1, s2)

if True:
    print(s1)
    print(test1)
    print(s2)
    print("---------------Diff-----------------")
    gamehop.stringDiff(s1, s2)
    print("------------------------------------")
