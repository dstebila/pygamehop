import ast
import inspect
import unittest

import gamehop.inlining

class myClassWithNoMethods():
    def __init__(self):
        self.myarg = 0

def f0(x: myClassWithNoMethods) -> int:
    return x.myarg


target0  = """def f0(x: myClassWithNoMethods) -> int:
    prefix_self_myarg = 0
    return prefix_self_myarg"""



class myClassWithAMethod():
    def __init__(self):
        self.myarg = 0
    def m(self, y: int):
        self.myarg = y

def f1(x: myClassWithAMethod, y: int) -> int:
    x.m(y)
    return x.myarg

target1 = """def f1(x: myClassWithAMethod, y: int) -> int:
    prefix_self_myarg = 0
    prefix_self_myarg = y
    return prefix_self_myarg"""



class myClassWithNoInit():
    def m(self, y: int):
        self.myarg = y
        return self.myarg

def f2(x: myClassWithNoInit, y: int) -> int:
    x.m(y)
    return x.myarg

target2 = """def f2(x: myClassWithNoInit, y: int) -> int:
    prefix_self_myarg = y
    return prefix_self_myarg"""



class myClassWithMethodWithoutArgument():
    def m(self):
        return 1 + 0

def f3(x: myClassWithMethodWithoutArgument) -> int:
    return x.m()

target3 = """def f3(x: myClassWithMethodWithoutArgument) -> int:
    return 1 + 0"""


class TestSomething(unittest.TestCase):
    def test_classWithNoMethods(self):
        self.assertEqual(
            target0,
            gamehop.inlining.inline_class(f0, 'x', myClassWithNoMethods)
        )        
    def test_classWithAMethod(self):
        self.assertEqual(
            target1,
            gamehop.inlining.inline_class(f1, 'x', myClassWithAMethod)
        )

    def test_classWithNoInit(self):
        self.assertEqual(
            target2,
            gamehop.inlining.inline_class(f2, 'x', myClassWithNoInit)
        )
    def test_classWithMethodWithNoArgument(self):
        self.assertEqual(
            target3,
            gamehop.inlining.inline_class(f3, 'x', myClassWithMethodWithoutArgument)
        )
