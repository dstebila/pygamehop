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

def inline_argument(f: Union[Callable, str], arg: str, val: Union[bool, float, int, str]) -> str:
    """Returns a string representing the provided function with the given argument inlined to the given value.  Works on values of type bool, float, int, or str.  Cannot handle cases where the variable to be inlined is assigned to."""
    fdef = internal.get_function_def(f)
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

def inline_function(inlinee: Union[Callable, str], inlinand: Union[Callable, str]) -> str:
    """Returns a string representing the second function inlined into the first.

    Only works on calls to the function in an Assign statement."""
    # get the function definitions
    inlinee_def = internal.get_function_def(inlinee)
    inlinand_def = copy.deepcopy(internal.get_function_def(inlinand))
    # check that the inlinand has only a single return as the last statement
    class ContainsReturn(ast.NodeVisitor):
        def visit_Return(self, node):
            raise NotImplementedError("Function to be inlined has a return statement somewhere other than the last line")
    for i in range(len(inlinand_def.body) - 1):
        ContainsReturn().visit(inlinand_def.body[i])
    if not isinstance(inlinand_def.body[-1], ast.Return): raise NotImplementedError("Function to be inlined does not end with a return statement")
    # define the inliner which will do the replacements
    class Inliner(ast.NodeTransformer):
        def __init__(self, inlinee_def, inlinand_def):
            self.inlinee_def = inlinee_def
            self.inlinand_def = inlinand_def
            self.variables_in_inlinee = internal.find_all_variables(inlinee_def)
            self.variables_in_inlinand = internal.find_all_variables(inlinand_def)
            self.replacement_count = 0
        def visit_Assign(self, stmt):
            if isinstance(stmt.value, ast.Call) and stmt.value.func.id == self.inlinand_def.name:
                self.replacement_count += 1
                # prefix all variables in inlinand
                mappings = dict()
                for var in self.variables_in_inlinand: 
                    mappings[var] = 'v_{:s}_{:d}_{:s}'.format(self.inlinand_def.name, self.replacement_count, var)
                newinlinand_def = internal.rename_variables(self.inlinand_def, mappings)
                # map the parameters onto the arguments
                assert len(stmt.value.args) == len(newinlinand_def.args.args)
                for i in range(len(stmt.value.args)):
                    arg = stmt.value.args[i]
                    if isinstance(arg, ast.Name):
                        mapping = {newinlinand_def.args.args[i].arg: stmt.value.args[i].id}
                        newinlinand_def = internal.rename_variables(newinlinand_def, mapping, error_if_exists = False)
                    elif isinstance(arg, ast.Constant):
                        newinlinand_def = internal.get_function_def(inline_argument(newinlinand_def, newinlinand_def.args.args[i].arg, stmt.value.args[i].value))
                    else: raise NotImplementedError("Don't know how to inline calls whose arguments are of type {:s}".format(type(arg).__name__))
                # turn the final return statement into an assignment
                assert isinstance(newinlinand_def.body[-1], ast.Return)
                newret = ast.Assign(targets=stmt.targets, value=newinlinand_def.body[-1].value)
                newinlinand_def.body[-1] = newret
                # output is the inlined function body
                return newinlinand_def.body
            else: return stmt
    # run the inliner
    newinlinee_def = Inliner(inlinee_def, inlinand_def).visit(inlinee_def)
    # if there's still a call to our function somewhere, it must have been somewhere other than on a bare Assign line; raise an error
    class ContainsCall(ast.NodeVisitor):
        def __init__(self, funcname):
            self.funcname = funcname
        def visit_Call(self, node):
            if node.func.id == self.funcname: raise NotImplementedError("Can't inline functions that are called on anything other than as a solitary assignment line, e.g., y = f(x)")
    ContainsCall(inlinand_def.name).visit(newinlinee_def)
    return ast.unparse(ast.fix_missing_locations(newinlinee_def))
