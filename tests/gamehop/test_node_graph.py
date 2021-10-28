import ast
import unittest
import gamehop.utils as utils
import gamehop.node_graph as ng
from gamehop.node_graph import Edge as Edge

def expected_result(f):
    fdef = utils.get_function_def(f)
    fdef.name = fdef.name.replace('_expected_result', '')
    return ast.unparse(fdef)

class TestNodeGraph(unittest.TestCase):
    def test_create_simple_graph(self):
        def f():
            x = 1
            y = x + 1
            return y


        fdef = utils.get_function_def(f)
        f_node = ast.parse(fdef)
        G = ng.Graph.from_stmts(f_node.body)
        self.assertEqual(len(G.vertices), 3)
        v0 = G.vertices[0]
        v1 = G.vertices[1]
        v2 = G.vertices[2]
        self.assertEqual(v0, f_node.body[0])
        self.assertEqual(v1, f_node.body[1])
        self.assertEqual(v2, f_node.body[2])

        self.assertEqual(len(G.edges), 2)
        self.assertEqual(G.edges[0].head, v0)
        self.assertEqual(G.edges[0].tail, v1)
        self.assertEqual(G.edges[1].head, v1)
        self.assertEqual(G.edges[1].tail, v2)
       
        self.assertEqual(G.in_neighbours(v0), [v1]) 
        self.assertEqual(G.in_neighbours(v1), [v2]) 
        self.assertEqual(G.in_neighbours(v2), []) 

        self.assertEqual(G.out_neighbours(v0), [ ]) 
        self.assertEqual(G.out_neighbours(v1), [v0]) 
        self.assertEqual(G.out_neighbours(v2), [v1]) 

        self.assertEqual(G.max_vertices(), [v2])

    def test_create_complex_graph_no_inner(self):
        def f():
            x = 1
            y = x + 1
            z = x + 2
            w = y + z
            return w + z + w + y


        fdef = utils.get_function_def(f)
        f_node = ast.parse(fdef)
        G = ng.Graph.from_stmts(f_node.body)
        self.assertEqual(len(G.vertices), 5)

        v0 = G.vertices[0]
        v1 = G.vertices[1]
        v2 = G.vertices[2]
        v3 = G.vertices[3]
        v4 = G.vertices[4]
        self.assertEqual(v0, f_node.body[0])
        self.assertEqual(v1, f_node.body[1])
        self.assertEqual(v2, f_node.body[2])
        self.assertEqual(v3, f_node.body[3])
        self.assertEqual(v4, f_node.body[4])

        self.assertEqual(G.edges, [ Edge(v1, v0, 'x'), 
                                    Edge(v2, v0, 'x'), 
                                    Edge(v3, v1, 'y'),
                                    Edge(v3, v2, 'z'),
                                    Edge(v4, v3, 'w'),
                                    Edge(v4, v2, 'z'),
                                    Edge(v4, v1, 'y')])

    def test_graph_DFS(self):
        def f():
            x = 1
            y = x + 1
            z = x + 2
            w = y + z
            return w + z + w + y


        fdef = utils.get_function_def(f)
        f_node = ast.parse(fdef)
        G = ng.Graph.from_stmts(f_node.body)

        v0 = G.vertices[0]
        v1 = G.vertices[1]
        v2 = G.vertices[2]
        v3 = G.vertices[3]
        v4 = G.vertices[4]

        new_body_stmts = [ s for s in G.depth_first_traverse([v4]) ]

        self.assertEqual(new_body_stmts, [ v4, v1, v0, v2, v3 ])

    def test_graph_topological_order_traverse(self):
        def f():
            x = 1
            y = x + 1
            z = x + 2
            w = y + z
            return w + z + w + y


        fdef = utils.get_function_def(f)
        f_node = ast.parse(fdef)
        G = ng.Graph.from_stmts(f_node.body)

        v0 = G.vertices[0]
        v1 = G.vertices[1]
        v2 = G.vertices[2]
        v3 = G.vertices[3]
        v4 = G.vertices[4]
        G.print()
        new_body_stmts = [ s for s in G.topological_order_traverse() ]

        self.assertEqual(new_body_stmts, [ v4, v3, v1, v2, v0 ])

    def test_graph_canonical_no_inner(self):
        def f():
            x = 1
            y = x + 1
            z = x + 2
            w = y + z
            return w + z + w + y


        fdef = utils.get_function_def(f)
        f_node = ast.parse(fdef)
        G = ng.Graph.from_stmts(f_node.body)

        v0 = G.vertices[0]
        v1 = G.vertices[1]
        v2 = G.vertices[2]
        v3 = G.vertices[3]
        v4 = G.vertices[4]

        G.canonical_sort()

        self.assertEqual(G.vertices, [ v0, v2, v1, v3, v4 ])


    def test_graph_if(self):
        def f():
            x = 1
            if x == 1:
                z = 2
            else:
                z = 3
            return z


        fdef = utils.get_function_def(f)
        f_node = ast.parse(fdef)
        G = ng.Graph.from_stmts(f_node.body)

        self.assertEqual(len(G.vertices), 3)
        v0 = G.vertices[0]
        v1 = G.vertices[1]
        v2 = G.vertices[2]

        G.print()
        self.assertEqual(v0, f_node.body[0])
        self.assertEqual(v1, f_node.body[1])
        self.assertEqual(v2, f_node.body[2])

        self.assertEqual(G.edges, [ Edge(v1, v0, 'x'),
                                    Edge(v2, v1, 'z')])

        body_graph = G.inner_graphs[v1]['body']
        orelse_graph = G.inner_graphs[v1]['orelse']

        self.assertEqual(len(body_graph.vertices), 1)
        self.assertEqual(len(orelse_graph.vertices), 1)


    def test_graph_function_def(self):
        def f():
            x = 1
            def g(y):
                z = x + y
                return z

            return g(1)

        fdef = utils.get_function_def(f)
        f_node = ast.parse(fdef)
        G = ng.Graph.from_stmts(f_node.body)
        v0 = G.vertices[0]
        v1 = G.vertices[1]
        v2 = G.vertices[2]
        Gb = G.inner_graphs[v1]['body']
        v3 = Gb.vertices[0]
        v4 = Gb.vertices[1]

        self.assertEqual(G.edges, [ Edge(v1, v0, 'x'), 
                                    Edge(v2, v1, 'g')])

        self.assertEqual(Gb.edges, [ Edge(v4, v3, 'z') ])

    def test_graph_function_def_reassign_variable(self):
        def f():
            x = 1
            def g(y):
                x = 3
                z = x + y
                return z

            return g(1) + x


        fdef = utils.get_function_def(f)
        f_node = ast.parse(fdef)
        G = ng.Graph.from_stmts(f_node.body)
        v0 = G.vertices[0]
        v1 = G.vertices[1]
        v2 = G.vertices[2]
        Gb = G.inner_graphs[v1]['body']
        v3 = Gb.vertices[0]
        v4 = Gb.vertices[1]
        v5 = Gb.vertices[2]
        G.print()
        self.assertEqual(G.edges, [ Edge(v2, v1, 'g'),
                                    Edge(v2, v0, 'x')])

        self.assertEqual(Gb.edges, [ Edge(v4, v3, 'x'),
                                     Edge(v5, v4, 'z')])

    def test_graph_if_canonical_order(self):
        def f():
            x = 1
            r = 1
            s = 1
            if x == 1:
                y = 1
                z = 2
                w = r + y + z
            else:
                y = 1
                z = 2
                w = s + z + y
            q = 3
            return q + x + z + y + w


        fdef = utils.get_function_def(f)
        f_node = ast.parse(fdef)
        G = ng.Graph.from_stmts(f_node.body)

        self.assertEqual(len(G.vertices), 6)
        v0 = G.vertices[0]
        v1 = G.vertices[1]
        v2 = G.vertices[2]
        v3 = G.vertices[3]
        v4 = G.vertices[4]
        v5 = G.vertices[5]
        v6 = G.inner_graphs[v3]['body'].vertices[0]
        v7 = G.inner_graphs[v3]['body'].vertices[1]
        v8 = G.inner_graphs[v3]['body'].vertices[2]
        v9 = G.inner_graphs[v3]['orelse'].vertices[0]
        v10 = G.inner_graphs[v3]['orelse'].vertices[1]
        v11 = G.inner_graphs[v3]['orelse'].vertices[2]

        # outer graph edges
        # not testing for extra edges because that is tested elsewhere
        G.print()
        self.assertEqual(G.edges, [ Edge(v3, v0, 'x'),
                                    Edge(v3, v1, 'r'),
                                    Edge(v3, v2, 's'),
                                    Edge(v5, v4, 'q'),
                                    Edge(v5, v0, 'x'),
                                    Edge(v5, v3, 'z'),
                                    Edge(v5, v3, 'y'),
                                    Edge(v5, v3, 'w')])

        Gb = G.inner_graphs[v3]['body']
        self.assertEqual(Gb.edges, [ Edge(v8, v6, 'y'),
                                     Edge(v8, v7, 'z')])

        Go = G.inner_graphs[v3]['orelse']
        self.assertEqual(Go.edges, [ Edge(v11, v10, 'z'),
                                     Edge(v11, v9,  'y')])


        G.canonical_sort()

        self.assertEqual(G.vertices, [v0, v1, v2, v4, v3, v5])
        self.assertEqual(Gb.vertices, [v6, v7, v8])
        self.assertEqual(Go.vertices, [v10, v9, v11])

    def test_canonical_sort_multiple_assigns(self):
        def f():
            a = 1
            b = a
            a = 2
            return a + b

        def f_expected_result():
            a = 1
            b = a
            a = 2
            return a + b

        fdef = utils.get_function_def(f)
        f_node = ast.parse(fdef)
        G = ng.Graph.from_stmts(f_node.body)
        G.print()
        G.canonical_sort()
        G.print()
        f_node.body = G.vertices
        self.assertEqual(ast.unparse(f_node), expected_result(f_expected_result))

    def test_canonical_sort_multiple_assigns_2(self):
        def f():
            a = 1
            a = 2
            b = a
            return a + b

        def f_expected_result():
            a = 1
            a = 2
            b = a
            return a + b

        fdef = utils.get_function_def(f)
        f_node = ast.parse(fdef)
        G = ng.Graph.from_stmts(f_node.body)
        G.canonical_sort()
        f_node.body = G.vertices
        self.assertEqual(ast.unparse(f_node), expected_result(f_expected_result))

    def test_omit_overwrite_edges_in_dfs(self):
        def f():
            a = 1
            a = 2
            b = a
            return a + b

        def f_expected_result():
            a = 2
            b = a
            return a + b

        fdef = utils.get_function_def(f)
        f_node = ast.parse(fdef)
        G = ng.Graph.from_stmts(f_node.body)
        start_vertex = G.vertices[-1]
        dfs_vertices = [v for v in G.depth_first_traverse([start_vertex], True) ] 
        G = G.induced_subgraph(dfs_vertices)
        G.canonical_sort()
        f_node.body = G.vertices
        
        self.assertEqual(ast.unparse(f_node), expected_result(f_expected_result))


    def test_reachable_subgraph_ignore_overwrites(self):
        def f():
            x = 1
            a = 1
            a = 2
            b = a
            return a + b

        def f_expected_result():
            a = 2
            b = a
            return a + b

        fdef = utils.get_function_def(f)
        f_node = ast.parse(fdef)
        G = ng.Graph.from_stmts(f_node.body)
        G = G.reachable_subgraph([ G.vertices[-1] ], True)
        G.canonical_sort()
        f_node.body = G.vertices
        
        self.assertEqual(ast.unparse(f_node), expected_result(f_expected_result))

    def test_reachable_subgraph_no_ignore_overwrites(self):
        def f():
            x = 1
            a = 1
            a = 2
            b = a
            return a + b

        def f_expected_result():
            a = 1
            a = 2
            b = a
            return a + b

        fdef = utils.get_function_def(f)
        f_node = ast.parse(fdef)
        G = ng.Graph.from_stmts(f_node.body)
        G = G.reachable_subgraph([ G.vertices[-1] ])
        G.canonical_sort()
        f_node.body = G.vertices
        self.assertEqual(ast.unparse(f_node), expected_result(f_expected_result))  

    def test_attribute_assignment(self):
        def A(): pass
        def C(): pass

        def f():
            (a, b) = A()
            c = C()
            c.x = a
            c.y = b
            return c

        def f_expected_result():
            (a, b) = A()
            c = C()
            c.x = a
            c.y = b
            return c


        fdef = utils.get_function_def(f)
        f_node = ast.parse(fdef)       
        G = ng.Graph.from_stmts(f_node.body)
        G.print()
        G = G.reachable_subgraph([ G.vertices[-1] ], True )
        G.print()
        G.canonical_sort()
        f_node.body = G.vertices
        self.assertEqual(ast.unparse(f_node), expected_result(f_expected_result))  


    def test_attribute_assignment_2(self):
        def A(): pass
        def C(): pass

        def f(c):
            a = A()
            a.b = c
            return a.e

        def f_expected_result(c):
            a = A()
            return a.e

        fdef = utils.get_function_def(f)
        f_node = ast.parse(fdef)       
        G = ng.Graph.from_stmts(f_node.body)
        G.print()
        G = G.reachable_subgraph([ G.vertices[-1] ], True )
        G.canonical_sort()
        f_node.body = G.vertices
        self.assertEqual(ast.unparse(f_node), expected_result(f_expected_result))  

    def test_canonical_sort_while(self):
        def f():
            a = 10 
            while a < 10:
                a = a + 1
                b = 1
            else:
                c = 1
            d = 1
            return a + b + c + d

        def f_expected_result():
            a = 10 
            while a < 10:
                a = a + 1
                b = 1
            else:
                c = 1
            d = 1
            return a + b + c + d

        fdef = utils.get_function_def(f)
        f_node = ast.parse(fdef)
        G = ng.Graph.from_stmts(f_node.body)
        G.print()
        G.canonical_sort()
        G.print()
        f_node.body = G.vertices
        self.assertEqual(ast.unparse(f_node), expected_result(f_expected_result))

    def test_canonical_sort_if2(self):
        def f():
            a = 10 
            if a < 10:
                a = a + 1
                b = 1
            else:
                a = 1
            d = 1
            return a + b + d

        def f_expected_result():
            a = 10 
            if a < 10:
                a = a + 1
                b = 1
            else:
                a = 1
            d = 1
            return a + b + d

        fdef = utils.get_function_def(f)
        f_node = ast.parse(fdef)
        G = ng.Graph.from_stmts(f_node.body)
        G.print()
        G.canonical_sort()
        G.print()
        f_node.body = G.vertices
        self.assertEqual(ast.unparse(f_node), expected_result(f_expected_result))


