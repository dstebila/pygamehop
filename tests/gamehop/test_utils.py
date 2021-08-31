import ast
import inspect
import unittest
import gamehop.utils

def expected_result(f):
    s = ast.unparse(gamehop.utils.get_function_def(f))
    s = s.replace('_expected_result', '')
    return  s

class TestNewNodeTransformer(unittest.TestCase):
    def test_prelude_statements(self):
        class NewNodeTester(gamehop.utils.NewNodeTransformer):

            def visit_Call(self, node):
                self.generic_visit(node)  # fix up all children _first_
                for i,a in enumerate(node.args):
                    if isinstance(a, ast.Call):
                        newvar = self.unique_variable_name()
                        newassign = ast.Assign(
                            targets = [ ast.Name(id = newvar, ctx = ast.Store) ],
                            value = a
                        )
                        self.add_prelude_statement(newassign)
                        node.args[i] = ast.Name(id = newvar, ctx = ast.Load)
                return node

        def a(): pass
        def b(): pass
        def c(): pass
        def f():
            x = a(b(c(1)))
            return x

        def f_expected_result():
            _var_0 = c(1)
            _var_1 = b(_var_0)
            x = a(_var_1)
            return x
        f_ast = ast.parse(gamehop.utils.get_function_def(f))
        nnt = NewNodeTester()
        f_new_ast = nnt.visit(f_ast)
        ast.fix_missing_locations(f_new_ast)
        f_transformed = ast.unparse(f_new_ast)

        self.assertEqual(f_transformed, expected_result(f_expected_result))
