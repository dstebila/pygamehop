import ast
import inspect
import unittest

import gamehop
import gamehop.verification

def f_inline_function_order_helper(x):
    return x + 1
class class_inline_function_order():
    def f(self):
        return f_inline_function_order_helper(1)        
def f_inline_function_order(v: class_inline_function_order):
    x = v.f()
    y = v.f()
    return y + 2 * x
def f_inline_function_order_expected_result():
    v0 = f_inline_function_order_helper(1)
    v1 = f_inline_function_order_helper(1)
    v2 = v0 + 2 * v1
    return v2

def f_constant_return(a, b, c):
    d = a + b
    return 1
def f_constant_return_expected_result():
    return 1

class class_inline_init_arg_helper():
    prop: 1
class class_inline_init_arg():
    def __init__(self, x: class_inline_init_arg_helper):
        self.x = x
def f_inline_init_arg(v: class_inline_init_arg, x: class_inline_init_arg_helper):
    return v.x.prop
def f_inline_init_arg_expected_result(v0: class_inline_init_arg_helper):
    v1 = v0.prop
    return v1
    
class class_inline_init_arg2_helper():
    prop: 1
class class_inline_init_arg2():
    def setCommonClass(self, x: class_inline_init_arg2_helper):
        self.x = x
def f_inline_init_arg2(v: class_inline_init_arg2, x: class_inline_init_arg2_helper):
    v.setCommonClass(x)
    return v.x.prop
def f_inline_init_arg2_expected_result(v0: class_inline_init_arg2_helper):
    v1 = v0.prop
    return v1

class class_inline_init_arg3_helper():
    prop: 1
class class_inline_init_arg3():
    x: None
def f_inline_init_arg3(v: class_inline_init_arg3, x: class_inline_init_arg3_helper):
    v.x = x
    return v.x.prop
def f_inline_init_arg3_expected_result(v0: class_inline_init_arg3_helper):
    v1 = v0.prop
    return v1


def expected_result(f):
    s = inspect.getsource(f)
    s = s.replace('_expected_result', '')
    return ast.unparse(ast.parse(s))

class TestCanonicalize(unittest.TestCase):
    def test_inline_function_order(self):
        f = gamehop.inline(f_inline_function_order, class_inline_function_order, 'v')
        s1 = gamehop.verification.canonicalize_function(f)
        f2 = gamehop.inlining.internal.get_function_def(f_inline_function_order_expected_result)
        gamehop.verification.canonicalization.canonicalize_function_name(f2)
        s2 = ast.unparse(f2)
        self.assertEqual(s1, s2)
    def test_constant_return(self):
        s1 = gamehop.verification.canonicalize_function(f_constant_return)
        f2 = gamehop.inlining.internal.get_function_def(f_constant_return_expected_result)
        gamehop.verification.canonicalization.canonicalize_function_name(f2)
        s2 = ast.unparse(f2)
        self.assertEqual(s1, s2)
    def test_inline_init_arg(self):
        test1 = gamehop.inlining.inline_class(f_inline_init_arg, 'v', class_inline_init_arg)
        s1 = gamehop.verification.canonicalize_function(test1)
        f2 = gamehop.inlining.internal.get_function_def(f_inline_init_arg_expected_result)
        gamehop.verification.canonicalization.canonicalize_function_name(f2)
        s2 = ast.unparse(f2)
        self.assertEqual(s1, s2)
    def test_inline_init_arg2(self):
        test1 = gamehop.inlining.inline_class(f_inline_init_arg2, 'v', class_inline_init_arg2)
        s1 = gamehop.verification.canonicalize_function(test1)
        f2 = gamehop.inlining.internal.get_function_def(f_inline_init_arg2_expected_result)
        gamehop.verification.canonicalization.canonicalize_function_name(f2)
        s2 = ast.unparse(f2)
        self.assertEqual(s1, s2)
    def test_inline_init_arg3(self):
        test1 = gamehop.inlining.inline_class(f_inline_init_arg3, 'v', class_inline_init_arg3)
        s1 = gamehop.verification.canonicalize_function(test1)
        f2 = gamehop.inlining.internal.get_function_def(f_inline_init_arg3_expected_result)
        gamehop.verification.canonicalization.canonicalize_function_name(f2)
        s2 = ast.unparse(f2)
        self.assertEqual(s1, s2)
