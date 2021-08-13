import ast
import inspect
import unittest

import gamehop.inlining.internal
import gamehop.verification.canonicalization

def f_basic(x, y):
    a = 7
    return y + b
f_basic_expected_result = """def f(x, y):
    a = 7
    return y + b"""

class TestCanonicalizeFunctionName(unittest.TestCase):
    def test_basic(self):
        f = gamehop.utils.get_function_def(f_basic)
        gamehop.verification.canonicalization.canonicalize_function_name(f)
        self.assertEqual(
            ast.unparse(f),
            f_basic_expected_result
        )
