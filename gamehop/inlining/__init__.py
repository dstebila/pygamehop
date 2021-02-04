import ast
import copy
import inspect
import types
from typing import Any, Callable, Union

from . import internal

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

def ast_from_literal(x: Union[bool, float, int, str, tuple, list, set]) -> ast.AST:
    if isinstance(x, bool) or isinstance(x, float) or isinstance(x, int) or isinstance(x, str):
        return ast.Constant(value=x)
    elif isinstance(x, tuple):
        return ast.Tuple(elts=[ast_from_literal(y) for y in x], ctx=ast.Load())
    elif isinstance(x, list):
        return ast.List(elts=[ast_from_literal(y) for y in x], ctx=ast.Load())
    elif isinstance(x, set):
        return ast.Set(elts=[ast_from_literal(y) for y in x], ctx=ast.Load())

def inline_argument(f: Union[Callable, str, ast.FunctionDef], arg: str, val: Union[bool, float, int, str, tuple, list, set, ast.AST]) -> str:
    """Returns a string representing the provided function with the given argument inlined to the given value.  Works on values of type bool, float, int, str, tuple, list, set, or an AST object.  Cannot handle cases where the variable to be inlined is assigned to."""
    fdef = internal.get_function_def(f)
    checkusage = IsNameNodeEverAssignedTo(arg)
    checkusage.visit(fdef)
    if checkusage.isassignedto: raise NotImplementedError("Cannot handle cases where the inlined variable is assigned to")
    # construct the new node
    if isinstance(val, bool) or isinstance(val, float) or isinstance(val, int) or isinstance(val, str) or isinstance(val, tuple) or isinstance(val, list) or isinstance(val, set):
        newnode = ast_from_literal(val)
    else:
        newnode = val
    newfdef = NameNodeReplacer(arg, newnode).visit(fdef)
    # remove the argument from the arguments list
    for a in newfdef.args.args:
        if a.arg == arg:
            newfdef.args.args.remove(a)
            break
    # return the resulting function
    return ast.unparse(ast.fix_missing_locations(newfdef))

def inline_function_helper_lines_of_inlined_function(prefix: str, call: ast.Call, inlinand_def: ast.FunctionDef):
    """Gets the lines of the body that result from expanding the call to 'call', with every local variable prefixed by prefix."""
    variables_in_inlinand = internal.find_all_variables(inlinand_def)
    # prefix all variables in inlinand
    mappings = dict()
    for var in variables_in_inlinand: 
        mappings[var] = '{:s}_{:s}'.format(prefix, var)
    newinlinand_def = internal.rename_variables(inlinand_def, mappings)
    # map the parameters onto the arguments
    assert len(call.args) == len(newinlinand_def.args.args)
    for i in range(len(call.args)):
        arg = call.args[i]
        if isinstance(arg, ast.Name):
            mapping = {newinlinand_def.args.args[i].arg: arg.id}
            newinlinand_def = internal.rename_variables(newinlinand_def, mapping, error_if_exists = False)
        elif isinstance(arg, ast.Constant):
            newinlinand_def = internal.get_function_def(inline_argument(newinlinand_def, newinlinand_def.args.args[i].arg, arg.value))
        else: raise NotImplementedError("Don't know how to inline calls whose arguments are of type {:s}".format(type(arg).__name__))
    return newinlinand_def.body

def inline_function(inlinee: Union[Callable, str, ast.FunctionDef], inlinand: Union[Callable, str, ast.FunctionDef]) -> str:
    """Returns a string representing (almost) all instances of the second function inlined into the first.  Only works on calls to bare assignments (y = f(x)) or bare calls (f(x))."""
    # get the function definitions
    inlinee_def = copy.deepcopy(internal.get_function_def(inlinee))
    inlinand_def = copy.deepcopy(internal.get_function_def(inlinand))
    # check that there are no return statements anywhere in the inlinand other than the last line
    class ContainsReturn(ast.NodeVisitor):
        def visit_Return(self, node):
            raise NotImplementedError("Function to be inlined has a return statement somewhere other than the last line")
    for i in range(len(inlinand_def.body) - 1):
        ContainsReturn().visit(inlinand_def.body[i])
    # if the last line of the inlinand is a return statement,
    # then we change it in to an assignment to a new variable called v_retval
    inlinand_has_return = False
    if isinstance(inlinand_def.body[-1], ast.Return):
        inlinand_has_return = True
        inlinand_def.body[-1] = ast.Assign(
            targets = [ast.Name(id='v_retval', ctx=ast.Store())],
            value = inlinand_def.body[-1].value
        )
    # go through every line of the 
    newinlinee_body = []
    replacement_count = 0
    for stmt in inlinee_def.body:
        # replace y = f(x)
        if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call) and isinstance(stmt.value.func, ast.Name) and stmt.value.func.id == inlinand_def.name:
            if not inlinand_has_return: raise ValueError("Trying to inline a function without a return statement into an assignment")
            # copy the expanded lines
            replacement_count += 1
            newinlinee_body.extend(inline_function_helper_lines_of_inlined_function('v_{:s}_{:d}'.format(inlinand_def.name, replacement_count), stmt.value, inlinand_def))
            # append an assignment for the return value
            newinlinee_body.append(ast.Assign(targets = stmt.targets, value = ast.Name(id='v_{:s}_{:d}_v_retval'.format(inlinand_def.name, replacement_count), ctx=ast.Load())))
        # replace f(x)
        elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call) and isinstance(stmt.value.func, ast.Name) and stmt.value.func.id == inlinand_def.name:
            if inlinand_has_return: raise ValueError("Trying to inline a function with a return statement into a standalone statement")
            # copy the expanded lines
            replacement_count += 1
            newinlinee_body.extend(inline_function_helper_lines_of_inlined_function('v_{:s}_{:d}'.format(inlinand_def.name, replacement_count), stmt.value, inlinand_def))
        else:
            newinlinee_body.append(stmt)
    inlinee_def.body = newinlinee_body
    # if there's still a call to our function somewhere, it must have been somewhere other than on a bare Assign line; raise an error
    class ContainsCall(ast.NodeVisitor):
        def __init__(self, funcname):
            self.funcname = funcname
        def visit_Call(self, node):
            if node.func.id == self.funcname: raise NotImplementedError("Can't inline functions that are called on anything other than as a solitary assignment line, e.g., y = f(x)")
    ContainsCall(inlinand_def.name).visit(inlinee_def)
    return ast.unparse(ast.fix_missing_locations(inlinee_def))

def inline_class(inlinee: Union[Callable, str], arg: str, inlinand: Union[object, str]) -> str:
    """Returns a string representing the given class definition inlined into an argument of the given function.."""
    pass
