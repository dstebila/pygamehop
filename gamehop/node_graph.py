import node_traverser as nt
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

    @staticmethod
    def from_stmts(stmts: List[ast.stmt]):
        '''Create a node graph from a list of statements.  Creates edges based on the relationship
        between nodes that store variables and those that load them'''
        G = Graph()
        # TODO finish this.  Need to make a NodeTraverser 
        return G

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

    def depth_first_traverse(self, v):
        yield self
        for n in self.out_neighbours(v):
            yield from n.depth_first_traverse(n)

    def topological_traverse(self):
        '''Returns the vertices in a topological ordering, starting from vertices that are not dependent on any variables'''
        max_vertices = [ v for v in self.vertices if len(self.out_edges[v]) == 0 ]
        for v in max_vertices:
            yield v

        vertices_remaining = [ v for v in self.vertices if v not in max_vertices ]
        yield from self.induced_subgraph(vertices_remaining).topological_traverse()

    def topological_sort(self):
        '''Sort the vertices in place according to a topological ordering.  Do this recursively on any inner graphs.'''
        vertices_in_order = self.topological_traverse()
        self.vertices = vertices_in_order
        for v in self.vertices:
            for field, inner_graph in self.inner_graphs[v]:
                inner_graph.topological_sort()

