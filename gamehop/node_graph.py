from . import node_traverser as nt
from . import utils
import ast
from typing import Dict, List


class Graph():
    def __init__(self):

        self.vertices: List[ast.AST] = list()

        # An edge goes from a Name load to a Name store
        # These dictionaries keep track in and out edges for each vertex
        self.in_edges: Dict[Dict[str, List[ast.AST]]] = dict() # first key = vertex, second key = variable name, value = list of vertices that reference that variable
        self.out_edges: Dict[Dict[str, ast.AST]] = dict() # first key = vertex, second key = variable name, value = the node that provides this value


        # This dictionary holds graphs corresponding to bodies of nodes
        # each value is a dictionar mapping node field names (eg. body, orelse) to inner graphs
        self.inner_graphs: Dict[ast.AST, Dict[str, Graph]] = dict()

        # For this graph, its values are loaded in the outer graph.  This will be put into order of loads during canonical ordering
        self.values_loaded: List[str] = list()

    @staticmethod
    def from_stmts(stmts: List[ast.stmt]):
        '''Create a node graph from a list of statements.  Creates edges based on the relationship
        between nodes that store variables and those that load them.  Recurses to create inner
        graphs on any statements that have bodies (eg. if body).  For now, does not do anything with function or class bodies.'''
        g_maker = GraphMaker()
        g_maker.visit_statements(stmts)
        return g_maker.graphs[0]

    def add_vertex(self, a: ast.stmt):
        self.vertices.append(a)
        self.in_edges[a] = dict()
        self.out_edges[a] = dict()

    def add_edge(self, s:ast.stmt, d: ast.stmt, var: str):
        '''Create an edge from vertex s to vertex d for variable var.  The edge indicates a dependency, i.e. vertex s depends
        on the value var assigned by vertex d.
        '''
        if var not in self.in_edges[d]:
            self.in_edges[d][var] = list()

        self.in_edges[d][var].append(s)
        self.out_edges[s][var] = d

    def induced_subgraph(self, newvertices: List[ast.AST]):
        '''Return a new graph which has newvertices as its vertices.  Edges are kept that go
        between vertices in newvertices'''
        G = Graph()
        for v in newvertices:
            G.vertices.append(v)
            G.in_edges[v] = { var: [ u for u in neighbours if u in newvertices ]  for var, neighbours in self.in_edges[v] }
            G.out_edges[v] = { var: neighbour for var, neighbour in self.out_edges[v] if neighbour in newvertices }
            # TODO: the above should always be the original out_edges for v unless v depends on some variable that is not assigned in newvertices, probably indicating a bug
            G.inner_graphs[v] = self.inner_graphs[v]
        return G

    def in_neighbours(self, v):
        return sum( [ v for k,v in self.in_edges[v]], [])

    def out_neighbours(self, v):
        return [ u for k, u in self.out_edges[v]]

    def var_refs(self, start = None):
        '''Returns variable names in order referenced by vertices, starting from a particular vertex (if supplied).  Note that
        if a vertex references several variables, they are returned in reverse order.  This is so that if this function output is
        reversed the order starts with the last statement (eg return) in order that it references the variables (left to right)'''
        i = self.vertices.index(start) if start is not None else 0
        for v in self.vertices[i:]:
            for varname in reversed(self.out_edges[v]):
                yield varname

    def depth_first_traverse(self, start_points, visited = list()):
        for v in start_points:
            if v not in visited:
                visited.append(v)
                yield v
                for n in self.out_neighbours(v):
                    yield from self.depth_first_traverse([n], visited)

    def cannical_order_traverse(self):
        '''Returns the vertices in a topological ordering, starting from vertices that are not dependent on any variables'''
        max_vertices = [ v for v in self.vertices if not self.out_edges[v] ]
        yield from max_vertices
        vertices_remaining = [ v for v in self.vertices if v not in max_vertices ]
        yield from self.induced_subgraph(vertices_remaining).topological_traverse()

    def canonical_sort(self):
        '''Sort the vertices in place according to a canonical ordering based on relationship between values stored and values loaded.
        Do this recursively on any inner graphs.'''
        # we reorder based on the out edges.  Out edges point towards where a value was assigned, i.e. backwards up the list of statements.


        # Step 1: Reorder by DFS from the whose values are not referenced (eg. return statement)
        # DFS spits out the vertices in this order: the return statement, the statement storing the first value
        # referenced by the return statement, the first value referenced by that one, etc. then
        # the statement which stored the second value referenced in the return statement etc.
        # If there is a return statement then this creates a deterministic ordering based on the
        # relationship between values stored and referenced.  But it is not topological ordering.

        # vertices whose values are not in this graph (eg. return statement), reversed.  Reverse so that most recent assignment to a variable comes first
        top_vertices = [ v for v in self.vertices if not self.out_edges[v] ].reverse()

        # put them in the order that they are referenced in the outer graph, reversed
        dfs_start_vertices = list()
        for var in reversed(self.values_loaded):
            for v in top_vertices:
                if var in self.in_edges[v]:
                    dfs_start_vertices.append(v)
                    break

        # we don't want to lose vertices if their variables were never referenced
        for v in top_vertices:
            if v not in dfs_start_vertices:
                dfs_start_vertices.append(v)

        vertices_dfs = [ v for v in self.depth_first_traverse(dfs_start_vertices) ]
        self.vertices = vertices_dfs


        # Step 2: Reorder vertices by Khan's algorithm
        # Khan's algorithm will not give a single possible ordering.  Where there are multiple possible orders, this code
        # will preserve the previous ordering from the DFS.
        vertices_in_order = [ v for v in self.topological_traverse() ]

        # we reorder based on the out edges.  Out edges point towards where a value was assigned, i.e. backwards up the list of statements.
        # here we put them in forwards order
        vertices_in_order.reverse()
        self.vertices = vertices_in_order

        # Between the DFS and Khan's algorithm we get a canonical ordering based only on the order that values are referenced
        # within a statement, and the relationship between statements that reference each other's values

        # recurse to any vertices that have inner graphs (eg. if body)
        for v in self.vertices:
            for field, inner_graph in self.inner_graphs[v]:

                # Outer graph statements are in order, so now update the inner graph's values_loaded
                # so that they are in order loaded
                values_in_order = [ var for var in self.var_refs(start = v) if var in inner_graph.values_loaded ]
                inner_graph.values_loaded = utils.remove_duplicates(values_in_order)

                inner_graph.canonical_sort()


class GraphMaker(nt.NodeTraverser):
    def __init__(self):
        # We keep a stack of graphs to store inner graphs as we create them
        self.graphs = [ Graph() ]
        super().__init__()

    def visit_stmt(self, stmt):
        # Visit children, and keep track of changes to the scope to see what
        # variables are loaded
        self.graphs[-1].add_vertex(stmt)
        old_scope = self.local_scope().copy()
        ret = super().visit_stmt(stmt)
        diff_scope = self.local_scope().diff(old_scope)

        # Create edges from this statement for every variable it loaded
        for var in diff_scope.vars_loaded:
            assigning_stmt = self.local_scope().var_value_assigner[var]
            self.graphs[-1].add_edge(stmt, assigning_stmt, var)

        return ret


    def visit_If_body(self, body):
        # Push a new graph for the body
        self.graphs.append(Graph())

        # Visit the body
        new_body = self.visit_stmts(body)

        # Pop the body's inner graph and assign as inner graph for the if
        body_graph = self.graphs.pop()
        self.graphs[-1].inner_graphs[self.parent()]['body'] = body_graph

        return new_body

    def visit_If_orelse(self, body):
        # Push a new graph for the orelse
        self.graphs.append(Graph())

        # Visit the orelse
        new_body = self.visit_stmts(body)

        # Pop the orelse's inner graph and assign as inner graph for the if
        orelse_graph = self.graphs.pop()
        self.graphs[-1].inner_graphs[self.parent()]['orelse'] = orelse_graph

        return new_body
