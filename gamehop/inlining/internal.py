import ast
import copy
import inspect
import types
from typing import Any, Callable, List, Optional, Set, Union

from .. import utils

def get_class_def(c: Union[Any, str, ast.ClassDef]) -> ast.ClassDef:
    """Gets the ast.ClassDef for a class that is given as a class or as a string."""
    # parse the function
    if isinstance(c, str): t = ast.parse(c)
    elif isinstance(c, ast.ClassDef): return c
    elif inspect.isclass(c): t = ast.parse(inspect.getsource(c))
    else: raise TypeError("Cannot handle classes provided as {:s}".format(type(c).__name__))
    # get the class definition
    cdef = t.body[0]
    assert isinstance(cdef, ast.ClassDef)
    return cdef

def find_all_variables(f: Union[Callable, str, ast.FunctionDef]) -> List[str]:
    """Return a set of all variables in the function, including function parameters."""
    fdef = utils.get_function_def(f)
    vars = list()
    # function arguments
    args = fdef.args
    if len(args.posonlyargs) > 0: raise NotImplementedError("No support for position-only variables")
    if len(args.kwonlyargs) > 0: raise NotImplementedError("No support for keyword-only variables")
    if len(args.kw_defaults) > 0: raise NotImplementedError("No support for keyword defaults")
    if len(args.defaults) > 0: raise NotImplementedError("No support for argument defaults")
    for arg in args.args:
        if arg.arg not in vars: vars.append(arg.arg)
    # find all assigned variables
    for stmt in fdef.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    if target.id not in vars: vars.append(target.id)
                elif isinstance(target, ast.Tuple) or isinstance(target, ast.List):
                    for elt in target.elts:
                        if isinstance(elt, ast.Name) and elt.id not in vars: vars.append(elt.id)
                # elif isinstance(target, ast.Attribute):
                #     attr_name = target.value.id + '.' + target.attr
                #     if attr_name not in vars: vars.append(attr_name)
                else:
                    raise NotImplementedError("Can't deal with assignment target type " + str(type(target)))
    return vars

def dereference_attribute(f: Union[Callable, str, ast.FunctionDef], name: str, formatstr: str) -> str:
    """Returns a string representing a function with all references to 'name.whatever' replaced with formatstr.format(whatever) (e.g., with 'name_whatever').  Only replaces top-level calls (a.b.c -> a_b.c) but not within (w.a.b does not go to w.a_b)."""
    fdef = copy.deepcopy(utils.get_function_def(f))
    # fortunately a.b.c is parsed as ((a.b).c)
    # and we only want to replace the a.b
    class AttributeDereferencer(ast.NodeTransformer):
        def __init__(self, name, formatstr):
            self.name = name
            self.formatstr = formatstr
        def visit_Attribute(self, node):
            # replace a.b
            if isinstance(node.value, ast.Name) and node.value.id == self.name:
                return ast.Name(id=formatstr.format(node.attr), ctx=node.ctx)
            # else if we're at the (a.b).c level,  we need to recurse into (a.b), 
            # replace there if needed, and then add the attribute c
            elif isinstance(node.value, ast.Attribute):
                return ast.Attribute(value=self.visit(node.value), attr=node.attr, ctx=node.ctx)
            # else: nothing to change
            else: return node
    return ast.unparse(ast.fix_missing_locations(AttributeDereferencer(name, formatstr).visit(fdef)))
