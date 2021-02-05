import unittest
import gamehop.inlining
import gamehop.verification

def somefunction(x):
    return x + 1

class myclass():
    prop: 12

def h(v: myclass):
    y = somefunction(v.prop)
    return y

def f_target():
    y = somefunction(12)
    return y


s1 = gamehop.verification.canonicalize_function(f_target)
test1 = gamehop.inlining.inline_class(h, 'v', myclass)
s2 = gamehop.verification.canonicalize_function(test1)


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
