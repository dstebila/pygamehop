import ast
import inspect
import unittest

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
