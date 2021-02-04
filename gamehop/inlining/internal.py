import ast
import copy
import inspect
import types
from typing import Callable, Set, Union

def get_function_def(f: Union[Callable, str, ast.FunctionDef]) -> ast.FunctionDef:
    """Gets the ast.FunctionDef for a function that is given as a function or as a string."""
    # parse the function
    if isinstance(f, types.FunctionType): t = ast.parse(inspect.getsource(f))
    elif isinstance(f, str): t = ast.parse(f)
    elif isinstance(f, ast.FunctionDef): return f
    else: raise TypeError("Cannot handle functions provided as {:s}".format(type(f).__name__))
    # get the function definition
    fdef = t.body[0]
    assert isinstance(fdef, ast.FunctionDef)
    return fdef

class NameRenamer(ast.NodeTransformer):
    """Replaces ids in Name nodes based on the provided mapping.  Raises a ValueError if the new name is already used in the function."""
    def __init__(self, mapping: dict, error_if_exists: bool):
        self.mapping = mapping
        self.error_if_exists = error_if_exists
    def visit_Name(self, node: ast.Name) -> ast.Name:
        if self.error_if_exists and (node.id in self.mapping.values()): raise ValueError("New name '{:s}' already exists in function".format(node.id))
        if node.id in self.mapping: return ast.Name(id=self.mapping[node.id], ctx=node.ctx)
        else: return node

def rename_variables(f: Union[Callable, str, ast.FunctionDef], mapping: dict, error_if_exists = True) -> ast.FunctionDef:
    """Returns a copy of the function with all the variables in the given function definition renamed based on the provided mapping.  Raises a ValueError if the new name is already used in the function."""
    retvalue = copy.deepcopy(get_function_def(f))
    # rename any relevant variables in the function arguments
    for arg in retvalue.args.args:
        if error_if_exists and (arg.arg in mapping.values()): raise ValueError("New name '{:s}' already exists in function".format(arg.arg))
        if arg.arg in mapping: arg.arg = mapping[arg.arg]
    # rename any relevant variables in the function body
    newbody = list()
    for stmt in retvalue.body:
        newbody.append(NameRenamer(mapping, error_if_exists).visit(stmt))
    retvalue.body = newbody
    return retvalue

def find_all_variables(f: Union[Callable, str, ast.FunctionDef]) -> Set[str]:
    """Return a set of all variables in the function, including function parameters."""
    fdef = get_function_def(f)
    vars = set()
    # function arguments
    args = fdef.args
    if len(args.posonlyargs) > 0: raise NotImplementedError("No support for position-only variables")
    if len(args.kwonlyargs) > 0: raise NotImplementedError("No support for keyword-only variables")
    if len(args.kw_defaults) > 0: raise NotImplementedError("No support for keyword defaults")
    if len(args.defaults) > 0: raise NotImplementedError("No support for argument defaults")
    for arg in args.args:
        vars.add(arg.arg)
    # find all assigned variables
    for stmt in fdef.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    vars.add(target.id)
                elif isinstance(target, ast.Tuple) or isinstance(target, ast.List):
                    for elt in target.elts:
                        if isinstance(elt, ast.Name): vars.add(elt.id)
                else:
                    raise NotImplementedError("Can't deal with assignment target type " + str(type(target)))
    return vars
