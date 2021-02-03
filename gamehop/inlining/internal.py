import ast
import copy
import inspect
import types
from typing import Callable, Union

def get_function_def(f: Union[Callable, str]) -> ast.FunctionDef:
    """Gets the ast.FunctionDef for a function that is given as a function or as a string."""
    # parse the function
    if isinstance(f, types.FunctionType): t = ast.parse(inspect.getsource(f))
    elif isinstance(f, str): t = ast.parse(f)
    else: raise TypeError("Cannot handle functions provided as {:s}".format(type(f).__name__))
    # get the function definition
    fdef = t.body[0]
    assert isinstance(fdef, ast.FunctionDef)
    return fdef

class NameRenamer(ast.NodeTransformer):
    """Replaces ids in Name nodes based on the provided mapping.  Raises a ValueError if the new name is already used in the function."""
    def __init__(self, mapping: dict):
        self.mapping = mapping
    def visit_Name(self, node: ast.Name) -> ast.Name:
        if node.id in self.mapping.values(): raise ValueError("New name '{:s}' already exists in function".format(node.id))
        if node.id in self.mapping: return ast.Name(id=self.mapping[node.id], ctx=node.ctx)
        else: return node

def rename_variables(fdef: ast.FunctionDef, mapping: dict) -> ast.FunctionDef:
    """Returns a copy of the function definition node with all the variables in the given function definition renamed based on the provided mapping.  Raises a ValueError if the new name is already used in the function."""
    retvalue = copy.deepcopy(fdef)
    # rename any relevant variables in the function arguments
    for arg in retvalue.args.args:
        if arg.arg in mapping.values(): raise ValueError("New name '{:s}' already exists in function".format(arg.arg))
        if arg.arg in mapping: arg.arg = mapping[arg.arg]
    # rename any relevant variables in the function body
    newbody = list()
    for stmt in retvalue.body:
        newbody.append(NameRenamer(mapping).visit(stmt))
    retvalue.body = newbody
    return retvalue
