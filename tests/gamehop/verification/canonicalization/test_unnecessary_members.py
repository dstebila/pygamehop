import ast
import inspect
import unittest

import gamehop.inlining.internal
import gamehop.verification.canonicalization.classes

def expected_result(c):
    cdef = gamehop.utils.get_class_def(c)
    cdef.name = cdef.name.replace('_expected_result', '')
    return ast.unparse(cdef)

class TestUnnecessaryMembers(unittest.TestCase):
    def test_basic(self):
        class C:
            def __init__(self):
                self.u = 1
                self.w = 3
            @staticmethod
            def potato(s):
                return s
            def chicken(self):
                return 7
            def beef(self):
                self.v = 4
                return self.u
        class C_expected_result:
            def __init__(self):
                self.u = 1
                self_w = 3
            @staticmethod
            def potato(s):
                return s
            def chicken(self):
                return 7
            def beef(self):
                self_v = 4
                return self.u
        c = gamehop.utils.get_class_def(C)
        gamehop.verification.canonicalization.classes.unnecessary_members(c)
        self.assertEqual(
            ast.unparse(c),
            expected_result(C_expected_result)
        )
    def test_with_oracle(self):
        class C:
            def chicken(self):
                return 7 + self.o_beef()
            def o_beef(self):
                return 5
        class C_expected_result:
            def chicken(self):
                return 7 + self.o_beef()
            def o_beef(self):
                return 5
        c = gamehop.utils.get_class_def(C)
        gamehop.verification.canonicalization.classes.unnecessary_members(c)
        self.assertEqual(
            ast.unparse(c),
            expected_result(C_expected_result)
        )
