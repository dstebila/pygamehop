import ast
import inspect
import unittest

import gamehop.inlining

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


class TestClassInlining(unittest.TestCase):
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
