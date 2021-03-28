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
    y = f_inline_function_order_helper(1)
    x = f_inline_function_order_helper(1)
    return y + 2 * x

def f_constant_return(a, b, c):
    d = a + b
    return 1
def f_constant_return_expected_result():
    r = 1
    return r

class class_inline_init_arg_helper():
    prop: 1
class class_inline_init_arg():
    def __init__(self, x: class_inline_init_arg_helper):
        self.x = x
def f_inline_init_arg(v: class_inline_init_arg, x: class_inline_init_arg_helper):
    return v.x.prop
def f_inline_init_arg_target(x: class_inline_init_arg_helper):
    return x.prop
    
class class_inline_init_arg2_helper():
    prop: 1
class class_inline_init_arg2():
    def setCommonClass(self, x: class_inline_init_arg2_helper):
        self.x = x
def f_inline_init_arg2(v: class_inline_init_arg2, x: class_inline_init_arg2_helper):
    v.setCommonClass(x)
    return v.x.prop
def f_inline_init_arg2_target(x: class_inline_init_arg2_helper):
    return x.prop

class class_inline_init_arg3_helper():
    prop: 1
class class_inline_init_arg3():
    x: None
def f_inline_init_arg3(v: class_inline_init_arg3, x: class_inline_init_arg3_helper):
    v.x = x
    return v.x.prop
def f_inline_init_arg3_target(x: class_inline_init_arg3_helper):
    return x.prop


def expected_result(f):
    s = inspect.getsource(f)
    s = s.replace('_expected_result', '')
    return ast.unparse(ast.parse(s))

class TestCanonicalize(unittest.TestCase):
    def test_inline_function_order(self):
        f = gamehop.inline(f_inline_function_order, class_inline_function_order, 'v')
        s1 = gamehop.verification.canonicalize_function(f)
        s2 = gamehop.verification.canonicalize_function(expected_result(f_inline_function_order_expected_result))
        self.assertEqual(s1, s2)
    def test_constant_return(self):
        s1 = gamehop.verification.canonicalize_function(f_constant_return)
        s2 = gamehop.verification.canonicalize_function(expected_result(f_constant_return_expected_result))
        self.assertEqual(s1, s2)
    def test_inline_init_arg(self):
        test1 = gamehop.inlining.inline_class(f_inline_init_arg, 'v', class_inline_init_arg)
        s1 = gamehop.verification.canonicalize_function(test1)
        s2 = gamehop.verification.canonicalize_function(f_inline_init_arg_target)
        self.assertEqual(s1, s2)
    def test_inline_init_arg2(self):
        test1 = gamehop.inlining.inline_class(f_inline_init_arg2, 'v', class_inline_init_arg2)
        s1 = gamehop.verification.canonicalize_function(test1)
        s2 = gamehop.verification.canonicalize_function(f_inline_init_arg2_target)
        self.assertEqual(s1, s2)
    def test_inline_init_arg3(self):
        test1 = gamehop.inlining.inline_class(f_inline_init_arg3, 'v', class_inline_init_arg3)
        s1 = gamehop.verification.canonicalize_function(test1)
        s2 = gamehop.verification.canonicalize_function(f_inline_init_arg3_target)
        self.assertEqual(s1, s2)
