#import node_traverser as nt
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
        # We reorder in two steps.
        # 
        # Step 1: Reorder by DFS from the whose values are not referenced (eg. return statement) 
        # DFS spits out the vertices in this order: the return statement, the statement storing the first value
        # referenced by the return statement, the first value referenced by that one, etc. then 
        # the statement which stored the second value referenced in the return statement etc.
        # If there is a return statement then this creates a deterministic ordering based on the 
        # relationship between values stored and referenced.  But it is not topological ordering.  
        # 
        # Step 2: Reorder vertices by Khan's algorithm
        # Khan's algorithm will not give a single possible ordering.  Where there are multiple possible orders, this code 
        # will preserve the previous ordering from the DFS.  
        #
        # Between the DFS and Khan's algorithm we get a canonical ordering based only on the order that values are referenced
        # within a statement, and the relationship between statements that reference each other's values

        # Initial order by DFS, starting from the vertices that are not referenced.  If this is a function with a
        # single return statement, and we have pruned unneeded vertices, then this will be the return statement.
        # this step will not remove any vertices since any vertices that are not referenced will be in final_vertices
        final_vertices = [ v for v in self.vertices if not self.out_edges[v] ]
        vertices_dfs = [ v for v in self.depth_first_traverse(final_vertices) ]
        self.ertices = vertices_dfs

        # Sort by Khan's algorithm
        vertices_in_order = [ v for v in self.topological_traverse() ]
        self.vertices = vertices_in_order

        # recurse to any vertices that have inner graphs (eg. if body)
        for v in self.vertices:
            for field, inner_graph in self.inner_graphs[v]:
                inner_graph.topological_sort()

