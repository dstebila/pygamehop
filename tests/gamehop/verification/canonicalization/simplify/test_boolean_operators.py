import ast
import inspect
import unittest

import gamehop.inlining.internal
import gamehop.verification.canonicalization.simplify as simplify

def f_andT(y):
    a = True and True and True
def f_andT_expected_result(y):
    a = True
def f_andF(y):
    a = True and False
def f_andF_expected_result(y):
    a = False
def f_orT(y):
    a = True or False or True
def f_orT_expected_result(y):
    a = True
def f_orF(y):
    a = False or False
def f_orF_expected_result(y):
    a = False
def f_manyT(y):
    a = True and (True or False) and (False or False or True)
def f_manyT_expected_result(y):
    a = True
def f_manyF(y):
    a = (False or (True and True)) and (True or (False and False)) and (False or (True and False))
def f_manyF_expected_result(y):
    a = False
def f_manyT_with_nonconst(y):
    a = True and (True or False) and (False or False or True or y)
def f_manyT_with_nonconst_expected_result(y):
    a = True
def f_manyF_with_nonconst(y):
    a = (False or (True and True and y)) and (True or (False and False)) and (False or (True and False))
def f_manyF_with_nonconst_expected_result(y):
    a = False


def expected_result(f):
    s = inspect.getsource(f)
    s = s.replace('_expected_result', '')
    return ast.unparse(ast.parse(s))

class TestSimplifyBooleanOperators(unittest.TestCase):
    def test_andT(self):
        f = gamehop.utils.get_function_def(f_andT)
        f = simplify.simplify(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_andT_expected_result)
        )
    def test_andF(self):
        f = gamehop.utils.get_function_def(f_andF)
        f = simplify.simplify(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_andF_expected_result)
        )
    def test_orT(self):
        f = gamehop.utils.get_function_def(f_orT)
        f = simplify.simplify(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_orT_expected_result)
        )
    def test_orF(self):
        f = gamehop.utils.get_function_def(f_orF)
        f = simplify.simplify(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_orF_expected_result)
        )
    def test_manyT(self):
        f = gamehop.utils.get_function_def(f_manyT)
        f = simplify.simplify(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_manyT_expected_result)
        )
    def test_manyF(self):
        f = gamehop.utils.get_function_def(f_manyF)
        f = simplify.simplify(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_manyF_expected_result)
        )
    def test_manyT_with_nonconst(self):
        f = gamehop.utils.get_function_def(f_manyT_with_nonconst)
        f = simplify.simplify(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_manyT_with_nonconst_expected_result)
        )
    def test_manyF_with_nonconst(self):
        f = gamehop.utils.get_function_def(f_manyF_with_nonconst)
        f = simplify.simplify(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_manyF_with_nonconst_expected_result)
        )
