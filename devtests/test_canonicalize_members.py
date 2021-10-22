import ast
import unittest

import gamehop.inlining.internal
import gamehop.verification.canonicalization

def expected_result(c):
    cdef = gamehop.utils.get_class_def(c)
    cdef.name = 'G'
    return ast.unparse(cdef)

class TestCanonicalizeMembers(unittest.TestCase):

    def test_keep_members_that_are_used(self):
        class C:
            def f(self):
                self.a = 1
                self.b = 2
                return True
            def g(self):
                return self.a + self.b
        class C_expected_result:
            def f(v0):
                v0.a = 1
                v0.b = 2
                return True
            def g(v0):
                v1 = v0.a + v0.b
                return v1
        c = gamehop.utils.get_class_def(C)
        s = gamehop.verification.canonicalize_game(c)
        self.assertEqual(s, expected_result(C_expected_result))

    def test_remove_unused_members(self):
        class C:
            def f(self):
                self.a = 1
                b = self.c()
                return b
            def g(self): return True
        class C_expected_result:
            def f(v0):
                v1 = v0.c()
                return v1
            def g(v0): return True
        c = gamehop.utils.get_class_def(C)
        s = gamehop.verification.canonicalize_game(c)
        self.assertEqual(s, expected_result(C_expected_result) )
