import ast
import inspect
import unittest

import gamehop.inlining.internal
import gamehop.verification.canonicalization

def f_basic(x, y):
    g = lambda z: z + 7 + x
    r = g(y)
    return r
def f_basic_expected_result(x, y):
    r = y + 7 + x
    return r

def expected_result(f):
    s = inspect.getsource(f)
    s = s.replace('_expected_result', '')
    return ast.unparse(ast.parse(s))

class TestCanonicalizeInlineLambda(unittest.TestCase):
    def test_basic(self):
        f = gamehop.utils.get_function_def(f_basic)
        gamehop.verification.canonicalization.inline_lambdas(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_basic_expected_result)
        )
