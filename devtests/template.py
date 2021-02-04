import ast
import inspect
import unittest

import gamehop.inlining.internal

f1 = "def f(x): return x"

f2 = "def f(x): return x"

class TestSomething(unittest.TestCase):
    def test_sometest(self):
        self.assertEqual(f1, f2)
