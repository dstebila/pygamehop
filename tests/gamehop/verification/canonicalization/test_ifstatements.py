import ast
import inspect
import unittest

import gamehop.inlining.internal
import gamehop.verification.canonicalization
import gamehop.verification.canonicalization.ifstatements


def f_basic_if(x):
    if x:
        z = 1
    else:
        z = 2
    return z
def f_basic_if_expected_result(x):
    body_0_z = 1
    orelse_0_z = 2
    (z) = (body_0_z) if x else (orelse_0_z)
    return z

def f_if_missing_vars(x):
    if x:
        w = 1
    else:
        z = 2
    return z
def f_if_missing_vars_expected_result(x):
    body_0_w = 1
    orelse_0_z = 2
    body_0_z = None
    orelse_0_w = None
    (w, z) = (body_0_w, body_0_z) if x else (orelse_0_w, orelse_0_z)
    return z



def expected_result(f):
    s = inspect.getsource(f)
    s = s.replace('_expected_result', '')
    return ast.unparse(ast.parse(s))

class TestIfStatementsToExpressions(unittest.TestCase):
    def test_basic1(self):
        f = gamehop.inlining.internal.get_function_def(f_basic_if)
        gamehop.verification.canonicalization.ifstatements.if_statements_to_expressions(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_basic_if_expected_result)
        )
    def test_if_missing_vars(self):
        f = gamehop.inlining.internal.get_function_def(f_if_missing_vars)
        gamehop.verification.canonicalization.ifstatements.if_statements_to_expressions(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_if_missing_vars_expected_result)
        )
