import ast
import inspect
import unittest

import gamehop.inlining.internal

def f_basic(x, y):
    a = 7
    b = len(x)
    c = b + y
    y = 4 + a
    (w, z) = (3, len(x))
    v, u = 4, len(x)
    return y + b
def f_attributed_assign(x, y):
    a = 7
    y.z = 3
    return y + a

class TestFindAllVariables(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(
            gamehop.inlining.internal.find_all_variables(f_basic),
            list(['x', 'y', 'a', 'b', 'c', 'w', 'z', 'v', 'u'])
        )
    def test_attributed_assign(self):
        with self.assertRaises(NotImplementedError):
            gamehop.inlining.internal.find_all_variables(f_attributed_assign)
