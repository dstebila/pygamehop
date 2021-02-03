import ast
import inspect
import types
from typing import Any, Callable, Union

__all__ = ['inline_argument']

class NameNodeReplacer(ast.NodeTransformer):
    """Replaces all instances of a Name node with a given node."""
    def __init__(self, id, val):
        self.id = id
        self.val = val
    def visit_Name(self, node):
        if node.id == self.id: return self.val
        else: return node

class IsNameNodeEverAssignedTo(ast.NodeVisitor):
    def __init__(self, id):
        self.id = id
        self.isassignedto = False
    def visit_Name(self, node):
        if node.id == self.id and isinstance(node.ctx, ast.Store): self.isassignedto = True

def inline_argument(f: Union[Callable, str], arg: str, val: Any):
    """Returns a string representing the provided function with the given argument inlined to the given value.  Works on values of type bool, float, int, or str.  Cannot handle cases where the variable to be inlined is assigned to."""
    # parse the function
    if isinstance(f, types.FunctionType): t = ast.parse(inspect.getsource(f))
    elif isinstance(f, str): t = ast.parse(f)
    else: raise TypeError("Cannot handle functions provided as {:s}".format(type(f).__name__))
    # get the function definition
    fdef = t.body[0]
    assert isinstance(fdef, ast.FunctionDef)
    checkusage = IsNameNodeEverAssignedTo(arg)
    checkusage.visit(fdef)
    if checkusage.isassignedto: raise NotImplementedError("Cannot handle cases where the inlined variabled is assigned to")
    # construct the new node
    if isinstance(val, bool) or isinstance(val, float) or isinstance(val, int) or isinstance(val, str):
        newnode = ast.Constant(value=val)
    else: raise NotImplementedError("No support yet for inlining arguments of type {:s}".format(type(val).__name__))
    newfdef = NameNodeReplacer(arg, newnode).visit(fdef)
    # remove the argument from the arguments list
    for a in newfdef.args.args:
        if a.arg == arg:
            newfdef.args.args.remove(a)
            break
    # return the resulting function
    return ast.unparse(ast.fix_missing_locations(newfdef))
