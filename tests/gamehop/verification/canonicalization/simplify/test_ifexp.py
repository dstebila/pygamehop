import ast
import inspect
import unittest

import gamehop.inlining.internal
import gamehop.verification.canonicalization.simplify as simplify

def f_ifexp(y):
    a = 1 if y else 2
    b = 1 if True else 2
    c = 1 if (3 == 4) else 2
    d = 1 if (3 <= 4) else 2
    e = 1 if (3 != 4) else 2
    f = 1 if (3 > 4) else 2
    g = 1 if (3 > 4) else 2 if (3 > 5) else 3
def f_ifexp_expected_result(y):
    a = 1 if y else 2
    b = 1
    c = 2
    d = 1
    e = 1
    f = 2
    g = 3


def expected_result(f):
    s = inspect.getsource(f)
    s = s.replace('_expected_result', '')
    return ast.unparse(ast.parse(s))

class TestSimplifyIfExp(unittest.TestCase):
    def test_ifexp(self):
        f = gamehop.inlining.internal.get_function_def(f_ifexp)
        f = simplify.ifexp(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_ifexp_expected_result)
        )
