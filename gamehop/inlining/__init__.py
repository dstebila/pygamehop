import ast
import copy
import inspect
import types
from typing import Any, Callable, List, Union

from . import internal

__all__ = ['inline_argument', 'inline_class', 'inline_function']

# Note that inlining uses Unicode symbols to make it look like the original code
# e.g. attribute dereferencing: x.y gets inlined to xⴰy
#      variables in an inlined function: def f(): a = y gets inlined to 
#      fᴠ1ⴰa (here the ᴠ1 denotes it's the first inlining of this function)
# https://www.asmeurer.com/python-unicode-variable-names/

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

def inline_function_helper_lines_of_inlined_function(prefix: str, call: ast.Call, inlinand_def: ast.FunctionDef, self_prefix="") -> list:
    """Gets the lines of the body that result from expanding the call to 'call', with every local variable prefixed by prefix. If self_prefix is specified, variables starting with SELF will be renamed using self_prefix instead of prefix."""
    newinlinand_def = copy.deepcopy(inlinand_def)
    variables_in_inlinand = internal.find_all_variables(inlinand_def)
    # prefix all variables in inlinand
    mappings = dict()
    for var in variables_in_inlinand: 
        if self_prefix != "" and var.startswith('SELF'): 
            mappings[var] = '{:s}ⴰ{:s}'.format(self_prefix, var[4:])
        else:
            mappings[var] = '{:s}ⴰ{:s}'.format(prefix, var)
    newinlinand_def = internal.rename_variables(newinlinand_def, mappings)
    # the above might miss instances of SELFwhatever in places other than assigns, so we rename them everywhere
    class SELFRename(ast.NodeTransformer):
        def __init__(self, self_prefix):
            self.self_prefix = self_prefix
        def visit_Name(self, node):
            if node.id.startswith('SELF'):
                return ast.Name(id='{:s}ⴰ{:s}'.format(self_prefix, node.id[4:]), ctx=node.ctx)
            else: return node
    newinlinand_def = SELFRename(self_prefix).visit(newinlinand_def)
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

def inline_function(inlinee: Union[Callable, str, ast.FunctionDef], inlinand: Union[Callable, str, ast.FunctionDef], search_function_name=None, dest_function_name=None, self_prefix="") -> str:
    """Returns a string representing (almost) all instances of the second function inlined into the first.  Only works on calls to bare assignments (y = f(x)) or bare calls (f(x)). Normally uses the inlinand's name as the name to search for and the name from which to build prefixes, but can be overridden by search_function_name and dest_function_name. If self_prefix is specified, variables starting with SELF will be renamed using self_prefix instead of prefix."""
    # get the function definitions
    inlinee_def = copy.deepcopy(internal.get_function_def(inlinee))
    inlinand_def = copy.deepcopy(internal.get_function_def(inlinand))
    if search_function_name == None: search_function_name = inlinand_def.name
    if dest_function_name == None: dest_function_name = inlinand_def.name
    # check that there are no return statements anywhere in the inlinand other than the last line
    class ContainsReturn(ast.NodeVisitor):
        def visit_Return(self, node):
            raise NotImplementedError("Function to be inlined ({:s}) has a return statement somewhere other than the last line".format(inlinand_def.name))
    for i in range(len(inlinand_def.body) - 1):
        ContainsReturn().visit(inlinand_def.body[i])
    # check if the last line of the inlinand is a return statement,
    inlinand_has_return = isinstance(inlinand_def.body[-1], ast.Return)
    # go through every line of the inlinee and replace all calls that we know how to handle
    newinlinee_body = []
    replacement_count = 0
    for stmt in inlinee_def.body:
        # replace y = f(x)
        if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call) and isinstance(stmt.value.func, ast.Name) and stmt.value.func.id == search_function_name:
            if not inlinand_has_return: raise ValueError("Trying to inline a function ({:s}) without a return statement into an assignment".format(inlinand_def.name))
            # copy the expanded lines
            replacement_count += 1
            newinlinee_body.extend(inline_function_helper_lines_of_inlined_function('{:s}ᴠ{:d}'.format(dest_function_name, replacement_count), stmt.value, inlinand_def, self_prefix))
            # assign the required variables based on the return statement
            newinlinee_body[-1] = ast.Assign(
                targets = stmt.targets, value = newinlinee_body[-1].value
            )
        # replace f(x)
        elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call) and isinstance(stmt.value.func, ast.Name) and stmt.value.func.id == search_function_name:
            if inlinand_has_return: raise ValueError("Trying to inline a function with a return statement into a standalone statement")
            # copy the expanded lines
            replacement_count += 1
            newinlinee_body.extend(inline_function_helper_lines_of_inlined_function('{:s}ᴠ{:d}'.format(dest_function_name, replacement_count), stmt.value, inlinand_def, self_prefix))
        else:
            newinlinee_body.append(stmt)
    inlinee_def.body = newinlinee_body
    # if there's still a call to our function somewhere, it must have been somewhere other than on a bare Assign line; raise an error
    class ContainsCall(ast.NodeVisitor):
        def __init__(self, funcname):
            self.funcname = funcname
        def visit_Call(self, node):
            if isinstance(node.func, ast.Name) and node.func.id == self.funcname: 
                raise NotImplementedError("Can't inline functions that are called on anything other than as a solitary assignment line, e.g., y = f(x)")
    ContainsCall(search_function_name).visit(inlinee_def)
    return ast.unparse(ast.fix_missing_locations(inlinee_def))

def inline_class(inlinee: Union[Callable, str, ast.FunctionDef], arg: str, inlinand: Union[object, str, ast.ClassDef], inline_init = True, inline_class_props = True) -> str:
    """Returns a string representing the given class definition inlined into an argument of the given function.."""
    # get the function definitions
    inlinee_def = copy.deepcopy(internal.get_function_def(inlinee))
    inlinand_def = copy.deepcopy(internal.get_class_def(inlinand))
    # inline class properties
    class_props_to_add: List[ast.stmt] = []
    if inline_class_props:
        for stmt in inlinand_def.body:
            if isinstance(stmt, ast.Assign):
                assert(isinstance(stmt.targets[0], ast.Name))
                newvarname = '{:s}ⴰ{:s}'.format(arg, stmt.targets[0].id)
                class_props_to_add.append(
                    ast.Assign(
                        [ast.Name(id=newvarname, ctx=ast.Store())],
                        stmt.value
                    )
                )
    # inline the __init__ method
    init_stmts_to_add: List[ast.stmt] = []
    if inline_init:
        for f in inlinand_def.body:
            if isinstance(f, ast.FunctionDef) and f.name == '__init__':
                initdef = copy.deepcopy(f)
                # dereference self.whatever in __init__
                formatstr = '{:s}ⴰ'.format(arg) + '{:s}'
                selfname = initdef.args.args[0].arg
                initdef = internal.get_function_def(internal.dereference_attribute(initdef, selfname, formatstr))
                # rename any of __init__'s (non-self) parameters and add them to inlinee's list of arguments
                for a in initdef.args.args[1:]:
                    newname = '{:s}ⴰinitⴰ{:s}'.format(arg, a.arg)
                    initdef = internal.rename_variables(initdef, {a.arg: newname})
                    newarg = copy.deepcopy(a)
                    newarg.arg = newname
                    inlinee_def.args.args.append(newarg)
                # copy the body of __init__ to the start of the inlinee body
                init_stmts_to_add = initdef.body
    inlinee_def.body = class_props_to_add + init_stmts_to_add + inlinee_def.body
    # dereference attribute calls in the new body
    formatstr = '{:s}ⴰ'.format(arg) + '{:s}'
    inlinee_def = internal.get_function_def(internal.dereference_attribute(inlinee_def, arg, formatstr))
    # inline all remaining methods
    for f in inlinand_def.body:
        if isinstance(f, ast.FunctionDef) and f.name != '__init__':
            fdef = copy.deepcopy(f)
            # dereference self.whatever in the function
            formatstr = 'SELF{:s}'
            selfname = fdef.args.args[0].arg
            fdef = internal.get_function_def(internal.dereference_attribute(fdef, selfname, formatstr))
            del fdef.args.args[0]
            # inline the method; we've already done the prefixing so we tell inline_function not to add its own prefixes
            inlinee_def = internal.get_function_def(inline_function(inlinee_def, fdef, search_function_name='{:s}ⴰ{:s}'.format(arg, fdef.name), dest_function_name='{:s}ⴰ{:s}'.format(arg, fdef.name), self_prefix='{:s}'.format(arg)))
    # remove the inlined argument from the inlinee's list of argments
    newargs = list()
    for i in range(len(inlinee_def.args.args)):
        if inlinee_def.args.args[i].arg != arg: 
            newargs.append(inlinee_def.args.args[i])
    inlinee_def.args.args = newargs
    return ast.unparse(ast.fix_missing_locations(inlinee_def))
