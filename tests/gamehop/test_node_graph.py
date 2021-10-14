import ast
import unittest
import gamehop.utils as utils
import gamehop.node_graph as ng

def expected_result(f):
    fdef = utils.get_function_def(f)
    fdef.name = fdef.name.replace('_expected_result', '')
    return ast.unparse(fdef)

class TestNodeGraph(unittest.TestCase):
    def test_creat_simple_graph(self):
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

        self.assertEqual(len(G.out_edges[v0].keys()), 0)
        self.assertEqual(len(G.out_edges[v1].keys()), 1)
        self.assertEqual(len(G.out_edges[v2].keys()), 1)
        self.assertEqual(G.out_edges[v1]['x'], v0)
        self.assertEqual(G.out_edges[v2]['y'], v1)

        self.assertEqual(len(G.in_edges[v0].keys()), 1)
        self.assertEqual(len(G.in_edges[v1].keys()), 1)
        self.assertEqual(len(G.in_edges[v2].keys()), 0)
        self.assertEqual(G.in_edges[v0]['x'], [v1])
        self.assertEqual(G.in_edges[v1]['y'], [v2])

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

        self.assertEqual(len(G.out_edges[v0].keys()), 0)
        self.assertEqual(len(G.out_edges[v1].keys()), 1)
        self.assertEqual(len(G.out_edges[v2].keys()), 1)
        self.assertEqual(len(G.out_edges[v3].keys()), 2)
        self.assertEqual(len(G.out_edges[v4].keys()), 3)
        self.assertEqual(G.out_edges[v1]['x'], v0)
        self.assertEqual(G.out_edges[v2]['x'], v0)
        self.assertEqual(G.out_edges[v3]['y'], v1)
        self.assertEqual(G.out_edges[v3]['z'], v2)
        self.assertEqual(G.out_edges[v4]['y'], v1)
        self.assertEqual(G.out_edges[v4]['z'], v2)
        self.assertEqual(G.out_edges[v4]['w'], v3)

        self.assertEqual(len(G.in_edges[v0].keys()), 1)
        self.assertEqual(len(G.in_edges[v1].keys()), 1)
        self.assertEqual(len(G.in_edges[v2].keys()), 1)
        self.assertEqual(len(G.in_edges[v3].keys()), 1)
        self.assertEqual(len(G.in_edges[v4].keys()), 0)
        self.assertEqual(G.in_edges[v0]['x'], [v1, v2])
        self.assertEqual(G.in_edges[v1]['y'], [v3, v4])
        self.assertEqual(G.in_edges[v2]['z'], [v3, v4])
        self.assertEqual(G.in_edges[v3]['w'], [v4])
        self.assertEqual(G.in_edges[v4], dict())

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

        self.assertEqual(new_body_stmts, [ v4, v3, v1, v0, v2 ])

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

        self.assertEqual(v0, f_node.body[0])
        self.assertEqual(v1, f_node.body[1])
        self.assertEqual(v2, f_node.body[2])

        self.assertEqual(len(G.out_edges[v0].keys()), 0)
        self.assertEqual(len(G.out_edges[v1].keys()), 1)
        self.assertEqual(len(G.out_edges[v2].keys()), 1)
        self.assertEqual(G.out_edges[v1]['x'], v0)
        self.assertEqual(G.out_edges[v2]['z'], v1)

        self.assertEqual(len(G.in_edges[v0].keys()), 1)
        self.assertEqual(len(G.in_edges[v1].keys()), 1)
        self.assertEqual(len(G.in_edges[v2].keys()), 0)
        self.assertEqual(G.in_edges[v0]['x'], [ v1 ])
        self.assertEqual(G.in_edges[v1]['z'], [ v2 ])

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

        self.assertEqual(G.out_edges[v1]['x'], v0)
        self.assertEqual(G.out_edges[v2]['g'], v1)

        self.assertEqual(Gb.out_edges[v4]['z'], v3)

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

        self.assertEqual(G.out_edges[v2]['x'], v0)
        self.assertEqual(G.out_edges[v2]['g'], v1)

        self.assertEqual(Gb.out_edges[v4]['x'], v3)
        self.assertEqual(Gb.out_edges[v5]['z'], v4)

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
            return q + x + z + y


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
        self.assertEqual(G.out_edges[v3]['x'], v0)
        self.assertEqual(G.out_edges[v3]['r'], v1)
        self.assertEqual(G.out_edges[v3]['s'], v2)
        self.assertEqual(G.out_edges[v5]['q'], v4)
        self.assertEqual(G.out_edges[v5]['x'], v0)
        self.assertEqual(G.out_edges[v5]['z'], v3)
        self.assertEqual(G.out_edges[v5]['y'], v3)

        Gb = G.inner_graphs[v3]['body']
        self.assertEqual(Gb.out_edges[v8]['y'], v6)
        self.assertEqual(Gb.out_edges[v8]['z'], v7)

        Go = G.inner_graphs[v3]['orelse']
        self.assertEqual(Go.out_edges[v11]['y'], v9)
        self.assertEqual(Go.out_edges[v11]['z'], v10)

        G.canonical_sort()

        self.assertEqual(G.vertices, [v2, v1, v0, v3, v4, v5])
        self.assertEqual(Gb.vertices, [v7, v6, v8])
        self.assertEqual(Go.vertices, [v9, v10, v11])

    # def test_canonical_sort_multiple_assigns(self):
        # def f():
            # a = 1
            # b = a
            # a = 2
            # return a + b

        # fdef = utils.get_function_def(f)
        # f_node = ast.parse(fdef)
        # G = ng.Graph.from_stmts(f_node.body)
        # G.canonical_sort()



