import ast
import unittest

import gamehop.utils

def expected_result(f):
    fdef = gamehop.utils.get_function_def(f)
    fdef.name = fdef.name.replace('_expected_result', '')
    return ast.unparse(fdef)


class TestAttributeNodeReplacer(unittest.TestCase):

    def test_one_level(self):
        def f(a, y): 
            v1 = a.b(y) # should be replaced
            v2 = a.b.c(y) # should be replaced
            v3 = a.a.b(y) # should not be replaced
            return v1 + v2 + v3
        def f_expected_result(a, y): 
            v1 = int(y)
            v2 = int.c(y)
            v3 = a.a.b(y)
            return v1 + v2 + v3
        x = gamehop.utils.AttributeNodeReplacer(['a', 'b'], 'int').visit(gamehop.utils.get_function_def(f))
        self.assertEqual(
            ast.unparse(x),
            expected_result(f_expected_result)
        )

    def test_two_level(self):
        def f(a, y): 
            v1 = a.b(y) # should not be replaced
            v2 = a.b.c(y) # should be replaced
            v3 = a.b.c.d(y) # should be replaced
            v4 = a.a.b.c(y) # should not be replaced
            return v1 + v2 + v3 + v4
        def f_expected_result(a, y):
            v1 = a.b(y)
            v2 = int(y)
            v3 = int.d(y)
            v4 = a.a.b.c(y)
            return v1 + v2 + v3 + v4
        x = gamehop.utils.AttributeNodeReplacer(['a', 'b', 'c'], 'int').visit(gamehop.utils.get_function_def(f))
        self.assertEqual(
            ast.unparse(x),
            expected_result(f_expected_result)
        )
