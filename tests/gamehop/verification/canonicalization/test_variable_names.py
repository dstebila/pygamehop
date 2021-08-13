import ast
import inspect
import unittest

import gamehop.inlining.internal
import gamehop.verification.canonicalization

def f_basic(x, y):
    a = 7
    return y + a
def f_basic_expected_result(v0, v1):
    v2 = 7
    return v1 + v2


def expected_result(f):
    s = inspect.getsource(f)
    s = s.replace('_expected_result', '')
    return ast.unparse(ast.parse(s))

class TestCanonicalizeVariableNames(unittest.TestCase):
    def test_basic(self):
        f = gamehop.utils.get_function_def(f_basic)
        gamehop.verification.canonicalization.canonicalize_variable_names(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_basic_expected_result)
        )
