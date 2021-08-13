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
    z = body_0_z if x else orelse_0_z
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
    orelse_0_w = None
    body_0_z = None
    ifcond_0 = x
    w = body_0_w if ifcond_0 else orelse_0_w
    z = body_0_z if ifcond_0 else orelse_0_z
    return z

def f_multiple_ifs(x):
    if x: w = 1
    else: w = 2
    if x == 3: w = 3
    else: w = 4
    return w
def f_multiple_ifs_expected_result(x):
    body_0_w = 1
    orelse_0_w = 2
    w = body_0_w if x else orelse_0_w
    body_1_w = 3
    orelse_1_w = 4
    w = body_1_w if x == 3 else orelse_1_w
    return w

def f_elif(x):
    if x == 1: w = 1
    elif x == 2: w = 2
    else: w = 3
    return w
def f_elif_expected_result(x):
    body_1_w = 1
    orelse_1_body_0_w = 2
    orelse_1_orelse_0_w = 3
    orelse_1_w = orelse_1_body_0_w if x == 2 else orelse_1_orelse_0_w
    body_1_body_0_w = None
    body_1_orelse_0_w = None
    ifcond_1 = x == 1
    w = body_1_w if ifcond_1 else orelse_1_w
    body_0_w = body_1_body_0_w if ifcond_1 else orelse_1_body_0_w
    orelse_0_w = body_1_orelse_0_w if ifcond_1 else orelse_1_orelse_0_w
    return w

def expected_result(f):
    s = inspect.getsource(f)
    s = s.replace('_expected_result', '')
    return ast.unparse(ast.parse(s))

class TestIfStatementsToExpressions(unittest.TestCase):
    def test_basic1(self):
        f = gamehop.utils.get_function_def(f_basic_if)
        gamehop.verification.canonicalization.ifstatements.if_statements_to_expressions(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_basic_if_expected_result)
        )
    def test_if_missing_vars(self):
        f = gamehop.utils.get_function_def(f_if_missing_vars)
        gamehop.verification.canonicalization.ifstatements.if_statements_to_expressions(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_if_missing_vars_expected_result)
        )
    def test_multiple_ifs(self):
        f = gamehop.utils.get_function_def(f_multiple_ifs)
        gamehop.verification.canonicalization.ifstatements.if_statements_to_expressions(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_multiple_ifs_expected_result)
        )
    def test_elif(self):
        f = gamehop.utils.get_function_def(f_elif)
        gamehop.verification.canonicalization.ifstatements.if_statements_to_expressions(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_elif_expected_result)
        )
