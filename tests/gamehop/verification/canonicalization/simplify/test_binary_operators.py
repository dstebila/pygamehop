import ast
import inspect
import unittest

import gamehop.inlining.internal
import gamehop.verification.canonicalization.simplify as simplify

def f_add(y):
    a = 3 + 4
    b = 0 + y
def f_add_expected_result(y):
    a = 7
    b = y
def f_sub(y):
    a = 3 - 4
    b = 0 - y
    c = y - 0
def f_sub_expected_result(y):
    a = -1
    b = -y
    c = y
def f_mult(y):
    a = 3 * 4
    b = 0 * y
    c = 1 * y
    d = y * -1
def f_mult_expected_result(y):
    a = 12
    b = 0
    c = y
    d = -y
def f_div(y):
    a = 6 / 2
    b = 0 / y
    c = y / 1
    d = y / -1
def f_div_expected_result(y):
    a = 3.0
    b = 0
    c = y
    d = -y
def f_floordiv(y):
    a = 6 // 2
    b = 7 // 3
    c = 0 // y
    d = y // 1
def f_floordiv_expected_result(y):
    a = 3
    b = 2
    c = 0
    d = y
def f_mod(y):
    a = 6 % 2
    b = 7 % 3
    c = 0 % y
    d = y % 1
def f_mod_expected_result(y):
    a = 0
    b = 1
    c = 0
    d = 0
def f_pow(y):
    a = 2 ** 3
    b = 2 ** y
    c = 1 ** y
    d = 0 ** y
    e = y ** 2
    f = y ** 1
    g = y ** 0
    h = 0 ** 0
def f_pow_expected_result(y):
    a = 8
    b = 2 ** y
    c = 1
    d = 0 ** y
    e = y ** 2
    f = y
    g = 1
    h = 1
def f_lshift(y):
    a = 6 << 2
    b = 6 << 1
    c = 6 << 0
    d = y << 2
    e = y << 1
    f = y << 0
    g = 2 << y
    h = 1 << y
    i = 0 << y
def f_lshift_expected_result(y):
    a = 24
    b = 12
    c = 6
    d = y << 2
    e = y << 1
    f = y
    g = 2 << y
    h = 1 << y
    i = 0
def f_rshift(y):
    a = 6 >> 2
    b = 6 >> 1
    c = 6 >> 0
    d = y >> 2
    e = y >> 1
    f = y >> 0
    g = 2 >> y
    h = 1 >> y
    i = 0 >> y
def f_rshift_expected_result(y):
    a = 1
    b = 3
    c = 6
    d = y >> 2
    e = y >> 1
    f = y
    g = 2 >> y
    h = 1 >> y
    i = 0
def f_bitor(y):
    a = 5 | 2
    b = 5 | 1
    c = 5 | 0
    d = y | 2
    e = y | 1
    f = y | 0
    g = 2 | y
    h = 1 | y
    i = 0 | y
def f_bitor_expected_result(y):
    a = 7
    b = 5
    c = 5
    d = y | 2
    e = y | 1
    f = y
    g = 2 | y
    h = 1 | y
    i = y
def f_bitxor(y):
    a = 5 ^ 2
    b = 5 ^ 1
    c = 5 ^ 0
    d = y ^ 2
    e = y ^ 1
    f = y ^ 0
    g = 2 ^ y
    h = 1 ^ y
    i = 0 ^ y
def f_bitxor_expected_result(y):
    a = 7
    b = 4
    c = 5
    d = y ^ 2
    e = y ^ 1
    f = y
    g = 2 ^ y
    h = 1 ^ y
    i = y
def f_bitand(y):
    a = 5 & 2
    b = 5 & 1
    c = 5 & 0
    d = y & 2
    e = y & 1
    f = y & 0
    g = 2 & y
    h = 1 & y
    i = 0 & y
def f_bitand_expected_result(y):
    a = 0
    b = 1
    c = 0
    d = y & 2
    e = y & 1
    f = 0
    g = 2 & y
    h = 1 & y
    i = 0


def expected_result(f):
    s = inspect.getsource(f)
    s = s.replace('_expected_result', '')
    return ast.unparse(ast.parse(s))

class TestSimplifyBinaryOperators(unittest.TestCase):
    def test_add(self):
        f = gamehop.utils.get_function_def(f_add)
        f = simplify.binary_operators(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_add_expected_result)
        )
    def test_sub(self):
        f = gamehop.utils.get_function_def(f_sub)
        f = simplify.binary_operators(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_sub_expected_result)
        )
    def test_mult(self):
        f = gamehop.utils.get_function_def(f_mult)
        f = simplify.binary_operators(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_mult_expected_result)
        )
    def test_div(self):
        f = gamehop.utils.get_function_def(f_div)
        f = simplify.binary_operators(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_div_expected_result)
        )
    def test_floordiv(self):
        f = gamehop.utils.get_function_def(f_floordiv)
        f = simplify.binary_operators(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_floordiv_expected_result)
        )
    def test_mod(self):
        f = gamehop.utils.get_function_def(f_mod)
        f = simplify.binary_operators(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_mod_expected_result)
        )
    def test_pow(self):
        f = gamehop.utils.get_function_def(f_pow)
        f = simplify.binary_operators(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_pow_expected_result)
        )
    def test_lshift(self):
        f = gamehop.utils.get_function_def(f_lshift)
        f = simplify.binary_operators(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_lshift_expected_result)
        )
    def test_rshift(self):
        f = gamehop.utils.get_function_def(f_rshift)
        f = simplify.binary_operators(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_rshift_expected_result)
        )
    def test_bitor(self):
        f = gamehop.utils.get_function_def(f_bitor)
        f = simplify.binary_operators(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_bitor_expected_result)
        )
    def test_bitxor(self):
        f = gamehop.utils.get_function_def(f_bitxor)
        f = simplify.binary_operators(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_bitxor_expected_result)
        )
    def test_bitand(self):
        f = gamehop.utils.get_function_def(f_bitand)
        f = simplify.binary_operators(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_bitand_expected_result)
        )
