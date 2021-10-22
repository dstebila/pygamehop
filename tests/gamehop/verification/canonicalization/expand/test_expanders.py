import ast
import inspect
import unittest
from typing import Type

import gamehop.inlining.internal
import gamehop.verification.canonicalization.expand as expand

def expected_result(f):
    fdef = gamehop.utils.get_function_def(f)
    fdef.name = fdef.name.replace('_expected_result', '')
    return ast.unparse(fdef)

class TestExpandCallArguments(unittest.TestCase):
    def test_lambda(self):
        ''' We have to be careful not to expand out the bodies of lambdas,
        because they make no sense when taken out of the lambda context: the
        arguments are not variables in scope outside the lambda body.

        Probably this doesn't matter since we now inline lambdas before expanding.
        '''
        def f():
            somef = lambda x: x + 1
            return somef(1)

        def f_expected_result():
            somef = lambda x: x + 1
            φ0 = somef(1)
            return φ0

        f = gamehop.utils.get_function_def(f)
        expand.expand_non_compact_expressions(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_expected_result)
        )
    def test_function_call_in_return(self):
        class Potato: pass
        def g(x):
            return x
        def f(z: Type[Potato]):
            return g(z)

        def f_expected_result(z: Type[Potato]):
            φ0 = g  (z)
            return φ0

        fdef = gamehop.utils.get_function_def(f)
        expand.expand_non_compact_expressions(fdef)

        s1 = ast.unparse(fdef)
        s2 = expected_result(f_expected_result)
        self.assertEqual(s1, s2)

    def test_function_call_in_if(self):
        def g(x):
            return x
        def f(z):
            if g(z):
                pass

        def f_expected_result(z):
            φ0 = g(z)
            if φ0:
                pass

        fdef = gamehop.utils.get_function_def(f)
        expand.expand_non_compact_expressions(fdef)

        s1 = ast.unparse(fdef)
        s2 = expected_result(f_expected_result)
        self.assertEqual(s1, s2)
