import unittest
import gamehop.inlining
import gamehop.verification

from gamehop.primitives import PKE

Scheme = PKE.PKEScheme

# This test is totally unfair!
# Use case is experiment in PKE takes a Scheme as an argument
# In another module, adversary etc. refers to PKE.Scheme
# Workaround is to use a type alias: Scheme = PKE.Scheme


def h(pke: PKE.PKEScheme):
    y = 1
    return y

def f_target(pke: Scheme):
    y = 1
    return y


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
