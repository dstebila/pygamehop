import ast
import inspect
import unittest

import gamehop.inlining.internal
import gamehop.verification.canonicalization

def f_constant(y):
    a = 7
    x = a
    return x
def f_constant_expected_result(y):
    a = 7
    x = 7
    return 7
def f_variable(y):
    a = y
    x = a
    return x
def f_variable_expected_result(y):
    a = y
    x = y
    return y
def f_reassign(y):
    a = y
    x = a
    g(x)
    a = 7
    x = a
    g(x)
def f_reassign_expected_result(y):
    a = y
    x = y
    g(y)
    a = 7
    x = 7
    g(7)
def f_tuple(y):
    x = 4
    z = y
    (a, b, c) = (x, y, z)
    g(a + 1, b + 2, c + 3, x + 4)
def f_tuple_expected_result(y):
    x = 4
    z = y
    (a, b, c) = (4, y, y)
    g(4 + 1, y + 2, y + 3, 4 + 4)
def f_tuple2():
    c = 1
    d = 2
    (a,b) = (c,d)
    return a
def f_tuple2_expected_result():
    c = 1
    d = 2
    (a,b) = (1,2)
    return 1
def f_tuple3(a, b):
    c = (a, b)
    (x, y) = c
    return x + y
def f_tuple3_expected_result(a, b):
    c = (a, b)
    (x, y) = (a, b)
    return a + b


def expected_result(f):
    fdef = gamehop.utils.get_function_def(f)
    fdef.name = fdef.name.replace('_expected_result', '')
    return ast.unparse(fdef)

class TestCollapseAssigns(unittest.TestCase):
    def test_constant(self):
        f = gamehop.utils.get_function_def(f_constant)
        gamehop.verification.canonicalization.collapse_useless_assigns(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_constant_expected_result)
        )
    def test_variable(self):
        f = gamehop.utils.get_function_def(f_variable)
        gamehop.verification.canonicalization.collapse_useless_assigns(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_variable_expected_result)
        )
    def test_reassign(self):
        f = gamehop.utils.get_function_def(f_reassign)
        gamehop.verification.canonicalization.collapse_useless_assigns(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_reassign_expected_result)
        )
    def test_tuple(self):
        f = gamehop.utils.get_function_def(f_tuple)
        gamehop.verification.canonicalization.collapse_useless_assigns(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_tuple_expected_result)
        )
    def test_tuple2(self):
        f = gamehop.utils.get_function_def(f_tuple2)
        gamehop.verification.canonicalization.collapse_useless_assigns(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_tuple2_expected_result)
        )
    def test_tuple3(self):
        f = gamehop.utils.get_function_def(f_tuple3)
        gamehop.verification.canonicalization.collapse_useless_assigns(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_tuple3_expected_result)
        )

    def test_basic(self):
        def f(x):
            if x:
                a = 1
            else:
                a = 2
            return a

        def f_expected_result(x):
            if x:
                a = 1
            else:
                a = 2
            return a

        fdef = gamehop.utils.get_function_def(f)
        gamehop.verification.canonicalization.collapse_useless_assigns(fdef)
        self.assertEqual(
            ast.unparse(fdef),
            expected_result(f_expected_result)
        )

    def test_attributes(self):
        def f():
            (a,b) = A()
            (c,d) = B()
            e = C()
            e.a = a
            e.b = c

        def f_expected_result():
            (a,b) = A()
            (c,d) = B()
            e = C()
            e.a = a
            e.b = c

        fdef = gamehop.utils.get_function_def(f)
        gamehop.verification.canonicalization.collapse_useless_assigns(fdef)
        self.assertEqual(
            ast.unparse(fdef),
            expected_result(f_expected_result)
        )

    def test_attribute_collapse(self):
        def g(): pass
        def f(z):
            a = g()
            a.b = z
            return a.b

        def f_expected_result(z):
            a = g()
            a.b = z
            return z 

        fdef = gamehop.utils.get_function_def(f)
        gamehop.verification.canonicalization.collapse_useless_assigns(fdef)
        self.assertEqual(
            ast.unparse(fdef),
            expected_result(f_expected_result)
        )

    def test_attribute_collapse_2(self):
        def g(): pass
        def f(z, x):
            a = g()
            a.b = z
            a.c = x
            return a.b

        def f_expected_result(z,x):
            a = g()
            a.b = z
            a.c = x
            return z 

        fdef = gamehop.utils.get_function_def(f)
        gamehop.verification.canonicalization.collapse_useless_assigns(fdef)
        self.assertEqual(
            ast.unparse(fdef),
            expected_result(f_expected_result)
        )


    def test_attribute_collapse_no(self):
        def g(): pass
        def f(z):
            a = g()
            a.b = z
            a = g()
            return a.b

        def f_expected_result(z):
            a = g()
            a.b = z
            a = g()
            return a.b 

        fdef = gamehop.utils.get_function_def(f)
        gamehop.verification.canonicalization.collapse_useless_assigns(fdef)
        self.assertEqual(
            ast.unparse(fdef),
            expected_result(f_expected_result)
        )


