import node_traverser as nt
import ast
from typing import Dict, List

class Vertex():
    def __init__(self, node: ast.AST):
        self.node = node
        # An edge goes from a Name load to a Name store or expression value.
        # The string __retval__ is used as the name for expression values 
        # eg. value returned by a function Call

        # These dictionaries keep track of which variables are referenced
        # and by which other vertices
        self.in_edges: Dict[str, List[ast.AST]] = dict() # key = variable name, value = list of nodes that reference it
        self.out_edges: Dict[str, ast.AST] = dict() # key = variable name, value = the node that provides this value

