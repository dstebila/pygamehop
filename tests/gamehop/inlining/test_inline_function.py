import ast
import inspect
import unittest

import gamehop.inlining

def inlinand(a, b):
    c = a + b
    return c
def inlinand_compound_return(a, b):
    c = a + b
    return c + 7
def inlinand_no_return_at_end(a, b):
    c = a + b
def inlinand_multiple_returns(a, b):
    if a: return b
    elif not(a): return a
    return a + b

def f_variable(x):
    y = inlinand(x, x)
    z = 2
def f_variable_expected_result(x):
    inlinandᴠ1ⴰc = x + x
    y = inlinandᴠ1ⴰc
    z = 2
def f_constant(x):
    y = inlinand(x, 3)
def f_constant_expected_result(x):
    inlinandᴠ1ⴰc = x + 3
    y = inlinandᴠ1ⴰc
def f_several_calls(x):
    w = inlinand(x, x)
    y = inlinand(x, x)
def f_several_calls_expected_result(x):
    inlinandᴠ1ⴰc = x + x
    w = inlinandᴠ1ⴰc
    inlinandᴠ2ⴰc = x + x
    y = inlinandᴠ2ⴰc
def f_compound_return(x):
    y = inlinand_compound_return(x, 3)
def f_compound_return_expected_result(x):
    inlinand_compound_returnᴠ1ⴰc = x + 3
    y = inlinand_compound_returnᴠ1ⴰc + 7
def f_inlinand_nested(x):
    y = inlinand(inlinand(x, 3), 4)
def f_inlinand_in_operation(x):
    y = inlinand(x, 3) + 4
def f_no_return_at_end_but_expected(a, b):
    y = inlinand_no_return_at_end(a, 3)
def f_no_assignment(a, b):
    inlinand_no_return_at_end(a, 3)
def f_no_assignment_expected_result(a, b):
    inlinand_no_return_at_endᴠ1ⴰc = a + 3
def f_no_assignment_with_return(a, b):
    inlinand(a, 3)

def expected_result(f):
    s = inspect.getsource(f)
    s = s.replace('_expected_result', '')
    return ast.unparse(ast.parse(s))

class TestInlineFunction(unittest.TestCase):
    def test_variable(self):
        self.assertEqual(
            gamehop.inlining.inline_function(f_variable, inlinand),
            expected_result(f_variable_expected_result))
    def test_constant(self):
        self.assertEqual(
            gamehop.inlining.inline_function(f_constant, inlinand),
            expected_result(f_constant_expected_result))
    def test_several_calls(self):
        self.maxDiff = None
        self.assertEqual(
            gamehop.inlining.inline_function(f_several_calls, inlinand),
            expected_result(f_several_calls_expected_result))
    def test_compound_return(self):
        self.assertEqual(
            gamehop.inlining.inline_function(f_compound_return, inlinand_compound_return),
            expected_result(f_compound_return_expected_result))
    def test_inlinand_nested(self):
        with self.assertRaises(NotImplementedError):
            gamehop.inlining.inline_function(f_inlinand_nested, inlinand)
    def test_inlinand_in_operation(self):
        with self.assertRaises(NotImplementedError):
            gamehop.inlining.inline_function(f_inlinand_in_operation, inlinand)
    def test_no_return_at_end_but_expected(self):
        with self.assertRaises(ValueError):
            gamehop.inlining.inline_function(f_no_return_at_end_but_expected, inlinand_no_return_at_end)
    def test_multiple_returns(self):
        with self.assertRaises(NotImplementedError):
            gamehop.inlining.inline_function(f_variable, inlinand_multiple_returns)
    def test_no_assignment_no_return(self):
        self.assertEqual(
            gamehop.inlining.inline_function(f_no_assignment, inlinand_no_return_at_end),
            expected_result(f_no_assignment_expected_result))
    def test_no_assignment_with_return(self):
        with self.assertRaises(ValueError):
            gamehop.inlining.inline_function(f_no_assignment_with_return, inlinand)
