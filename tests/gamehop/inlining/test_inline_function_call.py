import ast
import inspect
import unittest

import gamehop.inlining

def inlinand(a, b):
    c = a + b
    return c

def expected_result(f):
    fdef = gamehop.utils.get_function_def(f)
    fdef.name = fdef.name.replace('_expected_result', '')
    return ast.unparse(fdef)

class TestInlineFunction(unittest.TestCase):

    def test_variable(self):
        def f(x):
            y = inlinand(x, x)
            z = 2
        def f_expected_result(x):
            inlinandᴠ1ⴰc = x + x
            y = inlinandᴠ1ⴰc
            z = 2
        self.assertEqual(
            gamehop.inlining.inline_function_call(inlinand, f),
            expected_result(f_expected_result))

    def test_constant(self):
        def f(x): y = inlinand(x, 3)
        def f_expected_result(x):
            inlinandᴠ1ⴰc = x + 3
            y = inlinandᴠ1ⴰc
        self.assertEqual(
            gamehop.inlining.inline_function_call(inlinand, f),
            expected_result(f_expected_result))

    def test_several_calls(self):
        self.maxDiff = None
        def f(x):
            w = inlinand(x, x)
            y = inlinand(x, x)
        def f_expected_result(x):
            inlinandᴠ1ⴰc = x + x
            w = inlinandᴠ1ⴰc
            inlinandᴠ2ⴰc = x + x
            y = inlinandᴠ2ⴰc
        self.assertEqual(
            gamehop.inlining.inline_function_call(inlinand, f),
            expected_result(f_expected_result))

    def test_compound_return(self):
        def inlinand_compound_return(a, b):
            c = a + b
            return c + 7
        def f(x): y = inlinand_compound_return(x, 3)
        def f_expected_result(x):
            inlinand_compound_returnᴠ1ⴰc = x + 3
            y = inlinand_compound_returnᴠ1ⴰc + 7
        self.assertEqual(
            gamehop.inlining.inline_function_call(inlinand_compound_return, f),
            expected_result(f_expected_result))

    def test_inlinand_nested(self):
        def f(x): y = inlinand(inlinand(x, 3), 4)
        with self.assertRaisesRegex(ValueError, "Could not fully inline inlinand into f since f calls inlinand in an unsupported way; the only supported way is an assignment statement of the form foo = inlinand\\(bar\\)"):
            gamehop.inlining.inline_function_call(inlinand, f)

    def test_inlinand_in_operation(self):
        def f(x): y = inlinand(x, 3) + 4
        with self.assertRaisesRegex(ValueError, "Could not fully inline inlinand into f since f calls inlinand in an unsupported way; the only supported way is an assignment statement of the form foo = inlinand\\(bar\\)"):
            gamehop.inlining.inline_function_call(inlinand, f)

    def test_no_return_at_end_but_expected(self):
        def inlinand_no_return_at_end(a, b): c = a + b
        def f(a, b): y = inlinand_no_return_at_end(a, 3)
        with self.assertRaisesRegex(ValueError, "Cannot inline function inlinand_no_return_at_end into statement y = inlinand_no_return_at_end\\(a, 3\\) in function f since inlinand_no_return_at_end does not return anything"):
            gamehop.inlining.inline_function_call(inlinand_no_return_at_end, f)

    def test_multiple_returns(self):
        def inlinand_multiple_returns(a, b):
            if a: return b
            elif not(a): return a
            return a + b
        def f(x): y = inlinand_multiple_returns(x, x)
        with self.assertRaisesRegex(NotImplementedError, "Inlining function inlinand_multiple_returns into f since inlinand_multiple_returns contains a return statement somewhere other than the last line \\(namely, line 1\\)"):
            gamehop.inlining.inline_function_call(inlinand_multiple_returns, f)

    def test_no_assignment_with_return(self):
        def f(a, b): inlinand(a, 3)
        with self.assertRaisesRegex(ValueError, "Could not fully inline inlinand into f since f calls inlinand in an unsupported way; the only supported way is an assignment statement of the form foo = inlinand\\(bar\\)"):
            gamehop.inlining.inline_function_call(inlinand, f)

    def test_if_body(self):
        def f(a,b):
            r = 3
            if a: r = inlinand(a, b)
            return r
        def f_expected_result(a, b):
            r = 3
            if a:
                inlinandᴠ1ⴰc = a + b
                r = inlinandᴠ1ⴰc
            return r
        self.assertEqual(
            gamehop.inlining.inline_function_call(inlinand, f),
            expected_result(f_expected_result))

    def test_if_body_else(self):
        def f(a,b):
            r = 3
            if a: r = inlinand(a, b)
            else: r = inlinand(a, b)
            return r
        def f_expected_result(a, b):
            r = 3
            if a:
                inlinandᴠ1ⴰc = a + b
                r = inlinandᴠ1ⴰc
            else:
                inlinandᴠ2ⴰc = a + b
                r = inlinandᴠ2ⴰc
            return r
        self.assertEqual(
            gamehop.inlining.inline_function_call(inlinand, f),
            expected_result(f_expected_result))
