import ast
import inspect
import unittest

import gamehop.inlining.internal

def f0_1(x: int):
    return x

def f0_2(y: int):
    r =  f0_1(y)
    return r

target0 = """def f0_2(y: int):
    v_f0_1_1_v_retval = y
    r = v_f0_1_1_v_retval
    return r"""



class TestFunctionInlining(unittest.TestCase):
    def test_functionsWithArguments(self):
        self.assertEqual(
            target0,
            gamehop.inlining.inline_function(f0_2, f0_1)
        )
