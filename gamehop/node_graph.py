from . import node_traverser as nt
from . import bits
import ast
from typing import Dict, List
from collections import namedtuple

Edge = namedtuple('Edge', 'tail head label')

class Graph():
    def __init__(self):

        self.vertices: List[ast.stmt] = list()
        # An edge goes from the tail to the head, where the tail vertex reads a variable
        # and the head vertex points to a vertex that wrote/modified the variable.  The label
        # on each edge is the name of the variable.
        self.edges: List[Edge] = list()


        # This dictionary holds graphs corresponding to bodies of nodes
        # each value is a dictionar mapping node field names (eg. body, orelse) to inner graphs
        self.inner_graphs: Dict[ast.AST, Dict[str, Graph]] = dict()

        # For this graph, its values are loaded in the outer graph.  This will be put into order of loads during canonical ordering
        self.values_loaded: List[str] = list()

    @staticmethod
    def from_stmts(stmts: List[ast.stmt], extra_dependencies: Dict[str, List[str]] = {}):
        '''Create a node graph from a list of statements.  Creates edges based on the relationship
        between nodes that store variables and those that load them.  Recurses to create inner
        graphs on any statements that have bodies (eg. if body).  For now, does not do anything with function or class bodies.'''
        g_maker = GraphMaker(extra_dependencies)
        g_maker.visit_statements(stmts)
        return g_maker.graphs[0]

    def add_vertex(self, a: ast.stmt):
        self.vertices.append(a)

    def _add_Edge(self, e: Edge):
        assert(e.head in self.vertices)
        assert(e.tail in self.vertices)
        bits.append_if_unique(self.edges, e)

    def add_edge(self, tail:ast.stmt, head: ast.stmt, var: str) -> None:
        '''Create an edge from vertex s to vertex d for variable var.  The edge indicates a dependency, i.e. vertex s depends
        on the value var assigned by vertex d.
        '''
        self._add_Edge(Edge(tail, head, var))

    def induced_subgraph(self, newvertices: List[ast.stmt]) -> 'Graph':
        '''Return a new graph which has newvertices as its vertices.  Edges are kept that go
        between vertices in newvertices'''
        G = Graph()

        for v in newvertices:
            G.add_vertex(v)
            if v in G.inner_graphs:
                G.inner_graphs[v] = self.inner_graphs[v]

        for e in self.edges:
            if e.head in G.vertices and e.tail in G.vertices:
                    G._add_Edge(e)
        return G

    def in_edges(self, v: ast.stmt) -> List[Edge]: 
        return [ e for e in self.edges if e.head == v ]

    def out_edges(self, v: ast.stmt) -> List[Edge]: 
        return [ e for e in self.edges if e.tail == v ]

    def in_edge_labels(self, v: ast.stmt) -> List[str]:
        return bits.unique_elements([ e.label for e in self.in_edges(v) ])

    def in_neighbours(self, v):
        ''' For a give vertex v, return the statements u such that v assigned/modified 
        a variable that u depends on.  I.e. u -> v is an edge.'''
        return bits.unique_elements( [ e.tail for e in self.edges if e.head == v ] )

    def out_neighbours(self, v: ast.stmt, omit_overwrites=False) -> List[ast.stmt]:
        ''' For a give vertex v, return the statements u such that u assigned/modified 
        a variable that v depends on.  I.e. v -> u is an edge'''
        return bits.unique_elements([ e.head for e in self.edges if e.tail == v and not (omit_overwrites and e.label.endswith(':overwrite')) ])

    def var_refs(self, start = None):
        '''Returns variable names in order referenced/loaded by vertices, starting from a particular vertex (if supplied).  Note that
        if a vertex references several variables, they are returned in reverse order.  This is so that if this function output is
        reversed the order starts with the last statement (eg return) in order that it references the variables (left to right)'''

        # We assume that edges are added in order that the corresponding variables are referenced.
        i = self.vertices.index(start) if start is not None else 0
        for v in self.vertices[i:]:
            for e in reversed(self.out_edges(v)):
                yield e.label

    def max_vertices(self) -> List[ast.stmt]:
        ''' Returns a list of vertices such that they have no in-edges, i.e. no other vertex depends on them.'''
        return [ v for v in self.vertices if self.in_edges(v) == [] ]

    def depth_first_traverse(self, start_points, omit_overwrites=False):
        yield from self.depth_first_traverse_R(start_points, list(), omit_overwrites)

    def depth_first_traverse_R(self, start_points, visited, omit_overwrites):
        for v in start_points:
            if v not in visited:
                visited.append(v)
                yield v
                # Visit the neighbours in reversed order.  We are visiting the entire graph
                # somehow backwards (from start_points back to vertices they depend on) and
                # we want that if we reverse that we would have the first neighbours referenced
                # to come first
                for n in reversed(self.out_neighbours(v, omit_overwrites)):
                    yield from self.depth_first_traverse_R([n], visited, omit_overwrites)

    def reachable_subgraph(self, start_points, omit_overwrites=False):
        '''Returns a new graph which is the induced subgraph of the current graph on the set of vertices
        reachable from vertices in start_points.  If omit_overwrites is set to True then edges
        resulting from one statement overwriting a variable previously assigned by another statement are
        ignored.
        '''
        new_vertices = [v for v in self.depth_first_traverse(start_points, omit_overwrites) ]

        return self.induced_subgraph(new_vertices)

    def topological_order_traverse(self):
        '''Returns the vertices in a topological ordering, starting from vertices that have no in-edges, i.e. they do not provide
        any values loaded by other statements'''
        max_vertices = self.max_vertices()
        if max_vertices:
            yield from max_vertices
            vertices_remaining = [ v for v in self.vertices if v not in max_vertices ]
            yield from self.induced_subgraph(vertices_remaining).topological_order_traverse()

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
        top_vertices = self.max_vertices()
        top_vertices.reverse()
        # put them in the order that they are referenced in the outer graph, reversed
        dfs_start_vertices = list()
        for var in reversed(self.values_loaded):
            for v in top_vertices:
                if var in self.in_edge_labels(v):
                    dfs_start_vertices.append(v)
                    break

        # we don't want to lose vertices if their variables were never referenced
        for v in top_vertices:
            if v not in dfs_start_vertices:
                dfs_start_vertices.append(v)

        vertices_dfs = [ v for v in self.depth_first_traverse(dfs_start_vertices) ]
        assert(len(self.vertices) == len(vertices_dfs))
        self.vertices = vertices_dfs

        # Step 2: Reorder vertices by Khan's algorithm
        # Khan's algorithm will not give a single possible ordering.  Where there are multiple possible orders, this code
        # will preserve the previous ordering from the DFS.
        vertices_in_order = [ v for v in self.topological_order_traverse() ]

        # we reorder based on the out edges.  Out edges point towards where a value was assigned, i.e. backwards up the list of statements.
        # here we put them in forwards order
        vertices_in_order.reverse()
        self.vertices = vertices_in_order

        # Between the DFS and Khan's algorithm we get a canonical ordering based only on the order that values are referenced
        # within a statement, and the relationship between statements that reference each other's values

        # recurse to any vertices that have inner graphs (eg. if body)
        for v, in_graph in self.inner_graphs.items():
            for field, inner_graph in in_graph.items():

                # Outer graph statements are in order, so now update the inner graph's values_loaded
                # so that they are in order loaded
                values_in_order = [ var for var in self.var_refs(start = v) if var in inner_graph.values_loaded ]
                inner_graph.values_loaded = bits.unique_elements(values_in_order)

                inner_graph.canonical_sort()

    def print(self):
        vertex_number = { v: i for i, v in enumerate(self.vertices) }
        print('Vertices')
        print('-----------')
        for v in vertex_number:
            print(f'{vertex_number[v]}: {ast.unparse(v)}')

        print('Edges')
        print('-----------')
        for e in self.edges:
            print(f'{vertex_number[e.tail]}, { vertex_number[e.head]}, { e.label }')

        if self.inner_graphs: print('Inner graphs')
        for v, bodies in self.inner_graphs.items():
            print(v)
            for bodyname, bodygraph in bodies.items():
                print(bodyname)
                bodygraph.print()

class GraphMaker(nt.NodeTraverser):
    def __init__(self, extra_dependencies: Dict[str, List[str]] = {}):
        # We keep a stack of graphs to store inner graphs as we create them
        self.graphs = [ Graph() ]
        self.extra_dependencies = extra_dependencies
        super().__init__()

    def visit_stmt(self, stmt):
        # Visit children, and keep track of changes to the scope to see what
        # variables are loaded
        self.graphs[-1].add_vertex(stmt)
        old_scope = self.local_scope().copy()
        ret = super().visit_stmt(stmt)

        # Create edges from this statement for every variable it loaded
        stmt_scope = self.stmt_scopes[-1]
        # Add edges for any extra dependencies passed in
        for v in stmt_scope.external_vars:
            if v in self.extra_dependencies:
                stmt_scope.external_vars.extend(self.extra_dependencies[v])
        for var in stmt_scope.external_vars:
            # TODO: if referencing a variable that was never defined, this next line will fail, exception instead?
            # At this point, if this statement both loads and assigns to the same variable then the var_assigner points to this statement!  
            # Need to look at the scope previous to this statement to get the proper assigner.
            if old_scope.in_scope(var):
                modifier_stmts = old_scope.var_modifiers(var)
            else:
                modifier_stmts = list()     # in case we don't find it in scope, the rest won't die.
                for s in reversed(self.scopes[:-1]):
                    if s.in_scope(var):
                        modifier_stmts = s.var_modifiers(var)
                        break

            for modifier_stmt in modifier_stmts:
                # Statements with bodies may load and store the same variable in any order, so check.
                if modifier_stmt == stmt:
                    continue
                # if this is an inner graph, then the modifier may not
                # be in this graph.
                if modifier_stmt in self.graphs[-1].vertices:
                    self.graphs[-1].add_edge(stmt, modifier_stmt, var)
                else:
                    # Modifier was not in this block, so add this
                    # as an external variable to the parent statement to create an edge
                    # in the outer graph
                    self.stmt_scopes[-2].add_var_load(var, self.parent_statement())
            
        # Create edges from this statement for every variable that it stores
        # which was previously stored.  This is necessary to preserve
        # order.  Note that this is only necessary for variables
        # that are in the same scope.  If this is an inner scope, eg
        # FunctionDef then the overwritten variable reverts back
        # to the original value once we leave that scope.
        for var in stmt_scope.unique_vars_and_attributes_stored():
            var_name = var + ':overwrite'
            for old_assigner in old_scope.var_modifiers(var):
                # the old assigner might not be in this graph, eg. if this is an inner graph
                # In that case it should be handled by the parent statement.
                if old_assigner in self.graphs[-1].vertices:
                    self.graphs[-1].add_edge(stmt, old_assigner, var_name)

                    # we also need to add edges to any statement that previously
                    # loaded this variable since they need to come before this
                    # statement in order to have the correct value
                    for e in self.graphs[-1].in_edges(old_assigner):
                        if e.label == var and e.tail is not stmt:
                               self.graphs[-1].add_edge(stmt, e.tail, var_name)

        return ret


    def visit_body(self, body, body_name):
        # Push a new graph for the body
        self.graphs.append(Graph())

        # Visit the body
        new_body = self.visit_stmts(body)

        # Pop the body's inner graph and assign as inner graph for the parent node
        body_graph = self.graphs.pop()
        if self.parent() not in self.graphs[-1].inner_graphs:
            self.graphs[-1].inner_graphs[self.parent()] = dict()

        self.graphs[-1].inner_graphs[self.parent()][body_name] = body_graph

        return new_body

    def visit_If_body(self, body):
        return self.visit_body(body, 'body')

    def visit_If_orelse(self, body):
        return self.visit_body(body, 'orelse')

    def visit_While_body(self, body):
        return self.visit_body(body, 'body')

    def visit_While_orelse(self, body):
        return self.visit_body(body, 'orelse')

    def visit_FunctionDef(self, node):
         # Push a new graph for the orelse
        self.graphs.append(Graph())

        # Visit the orelse
        self.visit_stmts(node.body)

        # Pop the orelse's inner graph and assign as inner graph for the if
        body_graph = self.graphs.pop()

        if node not in self.graphs[-1].inner_graphs:
            self.graphs[-1].inner_graphs[node] = dict()
        self.graphs[-1].inner_graphs[node]['body'] = body_graph

        return node # not bothering to change the body since we should never change anything is this class
