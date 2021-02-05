import unittest
import gamehop.inlining
import gamehop.verification

def somefunction(x):
    return x + 1

class myclass():
    def f(self):
        return somefunction(1)
        
def h(v: myclass):
    x = v.f()
    y = v.f()
    return y + 2 * x

def f_target():
    y = somefunction(1)
    x = somefunction(1)
    return y + 2 * x


s1 = gamehop.verification.canonicalize_function(f_target)
test1 = gamehop.inlining.inline_class(h, 'v', myclass)
s2 = gamehop.verification.canonicalize_function(test1)


class TestClassInlineFunctionOrder(unittest.TestCase):
    def test_sometest(self):
        self.assertEqual(s1, s2)

if True:
    print(s1)
    print(test1)
    print(s2)
    print("---------------Diff-----------------")
    gamehop.verification.stringDiff(s1, s2)
    print("------------------------------------")
