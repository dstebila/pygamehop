import ast
import inspect
import unittest
import gamehop.utils as utils


def expected_result(f):
    fdef = utils.get_function_def(f)
    fdef.name = fdef.name.replace('_expected_result', '')
    return ast.unparse(fdef)

class TestTemplate(unittest.TestCase):
    def test_template(self):
        def f():
            return 1

        def f_expected_result(z):
            return 1

        fdef = utils.get_function_def(f)
        self.assertEqual(
            ast.unparse(fdef),
            expected_result(f_expected_result)
        )
