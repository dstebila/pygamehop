import ast
import inspect
import unittest

import gamehop.inlining.internal
import gamehop.verification.canonicalization

def expected_result(f):
    fdef = gamehop.utils.get_function_def(f)
    fdef.name = fdef.name.replace('_expected_result', '')
    return ast.unparse(fdef)

class TestCanonicalizeInlineLambda(unittest.TestCase):
    def test_basic(self):
        def f_basic(x, y):
            g = lambda z: z + 7 + x
            r = g(y)
            return r
        def f_basic_expected_result(x, y):
            g = lambda z: z + 7 + x
            r = y + 7 + x
            return r

        f = gamehop.utils.get_function_def(f_basic)
        gamehop.verification.canonicalization.inline_lambdas(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_basic_expected_result)
        )
