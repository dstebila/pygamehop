import ast
import inspect
import unittest

from gamehop.primitives import Crypto
import gamehop
import gamehop.verification
import gamehop.verification.canonicalization as canonicalization

class G(Crypto.Game):
    def main(self):
        self.k = 1
        r = run(self.o_test)
        return r
    def o_test(self, b):
        return self.k + b

class G_expected_result(Crypto.Game):
    def main(v0):
        v0.k = 1
        v1 = run(v0.o_test)
        return v1
    def o_test(v0, v1):
        v2 = v0.k + v1
        return v2

def expected_result(c):
    cdef = gamehop.utils.get_class_def(c)
    cdef.name = 'G'
    return ast.unparse(cdef)

class TestCanonicalizeGame(unittest.TestCase):

    def test_member(self):
        self.maxDiff = None
        c = gamehop.utils.get_class_def(G)
        s = gamehop.verification.canonicalize_game(c)
        self.assertEqual(s, expected_result(G_expected_result))
