import unittest
import gamehop
import gamehop.inlining
import gamehop.verification

class commonClass():
    prop: 1

class myclass():
    x: None

def h(v: myclass, x: commonClass):
    v.x = x
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
