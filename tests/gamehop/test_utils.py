import ast
import inspect
import unittest
import gamehop.utils

def expected_result(f):
    fdef = gamehop.utils.get_function_def(f)
    fdef.name = fdef.name.replace('_expected_result', '')
    return ast.unparse(fdef)


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

    def test_scopes(self):
        class NewNodeTester(gamehop.utils.NewNodeTransformer):
            def visit_Call(self, node):
                self.thescope = self.vars_in_scope()
                self.a_in_scope = self.in_scope('a')
                self.z_in_scope = self.in_scope('z')

        def g(): pass
        def f():
            a = 1
            def blarg():
                b = 1
                g(2)
            return x

        f_ast = ast.parse(gamehop.utils.get_function_def(f))
        nnt = NewNodeTester()
        f_new_ast = nnt.visit(f_ast)

        self.assertEqual(nnt.thescope, [ 'a', 'b' ])
        self.assertEqual(nnt.a_in_scope, True)
        self.assertEqual(nnt.z_in_scope, False)
        self.assertEqual(nnt.scopes, [[]])
        self.assertEqual(nnt.in_scope('a'), False)


    def test_scopes_if(self):
        class NewNodeTester(gamehop.utils.NewNodeTransformer):
            def visit_Call(self, node):
                if node.func.id == 'g':
                    self.if_scope = self.vars_in_scope()
                elif node.func.id == 'h':
                    self.orelse_scope = self.vars_in_scope()
                elif node.func.id == 'j':
                    self.end_scope = self.vars_in_scope()
                return node
        def f(t):
            a = 1
            if t:
                b = 5
                c = 2
                z = g()
            else:
                b = 3
                d = 2
                h()
            j()
            return x

        def f_expected_result(t):
            a = 1
            if t:
                b = 5
                c = 2
                z = g()
            else:
                b = 3
                d = 2
                h()
            j()
            return x

        f_ast = ast.parse(gamehop.utils.get_function_def(f))
        nnt = NewNodeTester()
        f_new_ast = nnt.visit(f_ast)
        ast.fix_missing_locations(f_new_ast)
        f_transformed = ast.unparse(f_new_ast)

        self.assertEqual(f_transformed, expected_result(f_expected_result))
        self.assertEqual(nnt.if_scope, [ 'a', 'b', 'c' ])
        self.assertEqual(nnt.orelse_scope, [ 'a', 'b', 'd' ])
        self.assertEqual(nnt.end_scope, [ 'a', 'b' ])

        f_ast = ast.parse(gamehop.utils.get_function_def(f))
        nnt = NewNodeTester()
        f_ast.body = nnt.visit_statements( f_ast.body )
        ast.fix_missing_locations(f_ast)
        f_transformed = ast.unparse(f_ast)

        self.assertEqual(f_transformed, expected_result(f_expected_result))
        self.assertEqual(nnt.if_scope, [ 'a', 'b', 'c' ])
        self.assertEqual(nnt.orelse_scope, [ 'a', 'b', 'd' ])
        self.assertEqual(nnt.end_scope, [ 'a', 'b' ])


class TestAttributeNodeReplacer(unittest.TestCase):

    def test_one_level(self):
        def f(a, y):
            v1 = a.b(y) # should be replaced
            v2 = a.b.c(y) # should be replaced
            v3 = a.a.b(y) # should not be replaced
            return v1 + v2 + v3
        def f_expected_result(a, y):
            v1 = int(y)
            v2 = int.c(y)
            v3 = a.a.b(y)
            return v1 + v2 + v3
        x = gamehop.utils.AttributeNodeReplacer(['a', 'b'], 'int').visit(gamehop.utils.get_function_def(f))
        self.assertEqual(
            ast.unparse(x),
            expected_result(f_expected_result)
        )

    def test_two_level(self):
        def f(a, y):
            v1 = a.b(y) # should not be replaced
            v2 = a.b.c(y) # should be replaced
            v3 = a.b.c.d(y) # should be replaced
            v4 = a.a.b.c(y) # should not be replaced
            return v1 + v2 + v3 + v4
        def f_expected_result(a, y):
            v1 = a.b(y)
            v2 = int(y)
            v3 = int.d(y)
            v4 = a.a.b.c(y)
            return v1 + v2 + v3 + v4
        x = gamehop.utils.AttributeNodeReplacer(['a', 'b', 'c'], 'int').visit(gamehop.utils.get_function_def(f))
        self.assertEqual(
            ast.unparse(x),
            expected_result(f_expected_result)
        )
