import ast
import unittest
import gamehop.utils as utils
import gamehop.node_traverser as nt
import gamehop.scope as scope

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
        ntr = nt.NodeTraverser()
        ntr.visit(fdef)
        self.assertEqual(
            ast.unparse(fdef),
            ast.unparse(fdef2),
        )

    def test_prelude_statements(self):
        class NewNodeTester(nt.NodeTraverser):

            def visit_Call(self, node):
                self.generic_visit(node)  # fix up all children _first_
                for i,a in enumerate(node.args):
                    if isinstance(a, ast.Call):
                        newvar = self.unique_variable_name()
                        newassign = ast.Assign(
                            targets = [ ast.Name(id = newvar, ctx = ast.Store()) ],
                            value = a
                        )
                        self.add_prelude_statement(newassign)
                        node.args[i] = ast.Name(id = newvar, ctx = ast.Load())
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
        f_ast = ast.parse(utils.get_function_def(f))
        nnt = NewNodeTester()
        f_new_ast = nnt.visit(f_ast)
        ast.fix_missing_locations(f_new_ast)
        f_transformed = ast.unparse(f_new_ast)

        self.assertEqual(f_transformed, expected_result(f_expected_result))

    def test_scopes(self):
        class NewNodeTester(nt.NodeTraverser):
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

        f_ast = ast.parse(utils.get_function_def(f))
        nnt = NewNodeTester()
        nnt.visit(f_ast)

        self.assertEqual(nnt.thescope, [ 'a', 'b' ])
        self.assertEqual(nnt.a_in_scope, True)
        self.assertEqual(nnt.z_in_scope, False)
        self.assertEqual(nnt.vars_in_scope(), ['f'])
        self.assertEqual(nnt.in_scope('a'), False)

    def test_scopes_values(self):
        class NewNodeTester(nt.NodeTraverser):
            def visit_Call(self, node):
                if node.func.id == 'g':
                    self.inscope_c_val = ast.unparse(self.var_value('c'))
                elif node.func.id == 'h':
                    self.outscope_c_val = self.var_value('c')
                elif node.func.id == 'j':
                    self.end_a_val = ast.unparse(self.var_value('a'))
                    self.end_b_val = self.var_value('b')
                    self.bogus_val = self.var_value('bogus')
                return node
        def g(): pass
        def h(): pass
        def j(): pass
        def f(t):
            a = 1
            def k():
                c = 1
                g()
            h()
            if t:
                b = 5
                c = 2
            else:
                b = 3
                d = 2
                h()
            j()
            return x

        f_ast = ast.parse(utils.get_function_def(f))
        nnt = NewNodeTester()
        nnt.visit(f_ast)

        self.assertEqual(nnt.inscope_c_val, '1')
        self.assertTrue(nnt.outscope_c_val is None)
        self.assertEqual(nnt.end_a_val, '1')
        self.assertTrue(nnt.end_b_val is None)
        self.assertTrue(nnt.bogus_val is None)


    def test_scopes_function(self):
        class NewNodeTester(nt.NodeTraverser):
            def visit_Call(self, node):
                if node.func.id == "j":
                    self.outer_scope_end = self.local_scope()

                return self.generic_visit(node)

        def j(): pass

        def f():
            x = 1
            def g(y):
                z = x + 1
                return z

            z = g(1)
            j()
            return z

        f_ast = ast.parse(utils.get_function_def(f))
        nnt = NewNodeTester()
        f_new_ast = nnt.visit(f_ast)
        self.assertEqual(nnt.outer_scope_end.names_in_scope(), ['x', 'g', 'z'])
        self.assertEqual(nnt.outer_scope_end.vars_in_scope(), ['x', 'g', 'z'])

    def test_scopes_if(self):
        class NewNodeTester(nt.NodeTraverser):
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

        f_ast = ast.parse(utils.get_function_def(f))
        nnt = NewNodeTester()
        f_new_ast = nnt.visit(f_ast)
        ast.fix_missing_locations(f_new_ast)
        f_transformed = ast.unparse(f_new_ast)

        self.assertEqual(f_transformed, expected_result(f_expected_result))
        self.assertEqual(nnt.if_scope, [ 't', 'a', 'b', 'c' ])
        self.assertEqual(nnt.orelse_scope, [ 't', 'a', 'b', 'd' ])
        self.assertEqual(nnt.end_scope, [ 't', 'a', 'b', 'c', 'z', 'd' ])

        f_ast = ast.parse(utils.get_function_def(f))
        nnt = NewNodeTester()
        f_ast.body = nnt.visit_statements( f_ast.body )
        ast.fix_missing_locations(f_ast)
        f_transformed = ast.unparse(f_ast)

        self.assertEqual(f_transformed, expected_result(f_expected_result))
        self.assertEqual(nnt.if_scope, [ 'a', 'b', 'c' ])
        self.assertEqual(nnt.orelse_scope, [ 'a', 'b', 'd' ])
        self.assertEqual(nnt.end_scope, [ 'a', 'b', 'c', 'z', 'd'  ])


    def test_scopes_tuple_values(self):
        class NewNodeTester(nt.NodeTraverser):
            def visit_Call(self, node):
                if node.func.id == 'g':
                    if not self.in_scope('a'): assert(False)
                    if not self.in_scope('b'): assert(False)
                    if not self.in_scope('c'): assert(False)
                    if not self.in_scope('d'): assert(False)
                    if not self.in_scope('e'): assert(False)
                    if not self.in_scope('f'): assert(False)
                    self.a = self.var_value('a').value
                    self.b = self.var_value('b').value
                    self.c = self.var_value('c').value
                    self.d = self.var_value('d').value
                    self.e = self.var_value('e').value
                    self.f = self.var_value('f').value

                return node
        def g(): pass
        def f(t):
            a = b = 1
            c, d = (1, 2)
            (e, f) = (3,4)
            g()

        f_ast = ast.parse(utils.get_function_def(f))
        nnt = NewNodeTester()
        nnt.visit(f_ast)

        self.assertEqual(nnt.a, 1)
        self.assertEqual(nnt.b, 1)
        self.assertEqual(nnt.c, 1)
        self.assertEqual(nnt.d, 2)
        self.assertEqual(nnt.e, 3)
        self.assertEqual(nnt.f, 4)

    def test_scopes_attributes(self):
        class NewNodeTester(nt.NodeTraverser):
            def visit_Call(self, node):
                if isinstance(node.func, ast.Attribute):
                    pass
                elif node.func.id == 'g':
                    assert('a' in self.vars_in_scope())
                elif node.func.id == 'h':
                    assert('a.b' in self.local_scope().vars_and_attributes_in_scope())
                    assert('a.b' not in self.local_scope().vars_in_scope())
                    assert(self.local_scope().var_value('a.b').value == 1)
                elif node.func.id == 'i':
                    assert('a.b' not in self.local_scope().vars_loaded)
                elif node.func.id == 'j':
                    assert('a.b.c' not in self.local_scope().vars_in_scope())
                elif node.func.id == 'k':
                    assert('a.b.c' not in self.local_scope().vars_loaded)
                elif node.func.id == 'l':
                    assert('a.blarg' not in self.local_scope().vars_loaded)
                    assert('a.blarg' not in self.local_scope().vars_in_scope())
                elif node.func.id == 'j':
                    assert('a.d' not in self.local_scope().vars_in_scope())
                    assert('a.e' not in self.local_scope().vars_in_scope())

                return self.generic_visit(node)

        class thing:
            def __init__(self):
                pass

        def f():
            a = object()
            g()
            a.b = 1
            h()
            c = a.b
            i()
            a.b.c = 1
            j()
            q = a.b.c
            k()
            a.blarg()
            l()
            (a.d, a.e) = (True, False)
            j()


        f_ast = ast.parse(utils.get_function_def(f))
        nnt = NewNodeTester()
        nnt.visit(f_ast)


    def test_parents(self):
        class NewNodeTester(nt.NodeTraverser):
            def visit_Call(self, node):
                if node.func.id == 'g':
                    self.g_call_parent_type = type(self.parent()).__name__
                elif node.func.id == 'h':
                    self.h_call_parent_type = type(self.parent()).__name__
                elif node.func.id == 'j':
                    self.j_call_parent_type = type(self.parent()).__name__
                return node
        def g(): pass
        def h(): pass
        def j(): pass

        def f():
            g()
            if h():
                pass
            x = j()

        f_ast = ast.parse(utils.get_function_def(f))
        nnt = NewNodeTester()
        f_ast = nnt.visit( f_ast )

        self.assertEqual(nnt.g_call_parent_type, 'Expr')
        self.assertEqual(nnt.h_call_parent_type, 'If')
        self.assertEqual(nnt.j_call_parent_type, 'Assign')

    def test_nodes_basic(self):
        def g(): pass
        def h(): pass
        def f():
            g()
            h(g())
            h()
        f_ast = ast.parse(utils.get_function_def(f))
        node_names = [ type(node).__name__ for node in nt.nodes(f_ast)]
        self.assertEqual(
            node_names,
            [ 'FunctionDef','arguments', 'Expr', 'Call', 'Name', 'Load',
            'Expr', 'Call', 'Name', 'Load', 'Call', 'Name', 'Load', 'Expr',
            'Call', 'Name', 'Load']
       )

    def test_nodes_type_filtered(self):
        def g(): pass
        def h(): pass
        def f():
            g()
            h(g())
            h()
        f_ast = ast.parse(utils.get_function_def(f))
        node_names = [ node.id for node in nt.nodes(f_ast, nodetype = ast.Name)]
        self.assertEqual(
            node_names,
            [ 'g', 'h', 'g', 'h' ]
       )

    def test_if_same_value(self):
        class NewNodeTester(nt.NodeTraverser):
            def visit_Call(self, node):
                if node.func.id == 'g':
                    self.a_val = self.var_value('a')
                return node


        def g(): pass

        def f(t,u):
            if t:
                a = u
            else:
                a = u
            g(a)

        nnt = NewNodeTester()
        f_ast = ast.parse(utils.get_function_def(f))
        nnt.visit(f_ast)
        self.assertEqual(ast.unparse(nnt.a_val), 'u')

    def test_while_scopes(self):
        class NewNodeTester(nt.NodeTraverser):
            def visit_Call(self, node):
                if node.func.id == 'g':
                    ls = self.local_scope()
                    assert(ls.var_value('s') is None)
                    assert(ls.var_value('t') is None)
                return node

        def g(): pass
        def f():
            s = 0
            while t > 0:
                t = t - 1
                s = s + 1
            else:
                s = -1
            g()
            return s

        nnt = NewNodeTester()
        f_ast = ast.parse(utils.get_function_def(f))
        nnt.visit(f_ast)



