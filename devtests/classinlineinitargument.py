import unittest
import gamehop
import gamehop.inlining
import gamehop.verification

class commonClass():
    prop: 1

class myclass():
    def __init__(self, x: commonClass):
        self.x = x

def h(v: myclass, x: commonClass):
    return v.x.prop

def f_target(x: commonClass):
    return x.prop


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
    gamehop.stringDiff(s1, s2)
    print("------------------------------------")
