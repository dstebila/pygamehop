import ast
import inspect
import unittest
import gamehop.utils as utils
from gamehop.node_traverser import *


def expected_result(f):
    fdef = utils.get_function_def(f)
    fdef.name = fdef.name.replace('_expected_result', '')
    return ast.unparse(fdef)

class TestNodeTraverser(unittest.TestCase):
    def test_no_changes(self):
        def f(z):
            return z

        fdef = utils.get_function_def(f)
        fdef2 = utils.get_function_def(f)
        nt = NodeTraverser()
        nt.visit(fdef)
        self.assertEqual(
            ast.unparse(fdef),
            ast.unparse(fdef2),
        )
