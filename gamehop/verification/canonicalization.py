import ast
import secrets
from typing import List, Union

from ..inlining import internal

def canonicalize_function_name(f: ast.FunctionDef, name = 'f') -> None:
    """Modify (in place) the given function definition to have a canonical name."""
    f.name = name
    ast.fix_missing_locations(f)

def canonicalize_return(f: ast.FunctionDef) -> None:
    """Modify (in place) the given function definition to simplify its return statement to be either a constant or a single variable."""
    class ReturnExpander(ast.NodeTransformer):
        def __init__(self, vars, prefix = 'ret'):
            self.vars = vars
            self.prefix = prefix
        def visit_Return(self, node):
            # if it directly returns a constant or variable, consider that canonical
            if isinstance(node.value, ast.Constant): return node
            if isinstance(node.value, ast.Name): return node
            # otherwise, make a new assignment for that return value and then return the newly assigned variable
            # find a unique name for the return value
            i = 0
            retname = '{:s}{:d}'.format(self.prefix, i)
            while retname in self.vars:
                i += 1
                retname = '{:s}{:d}'.format(self.prefix, i)
            self.vars.append(retname)
            assign = ast.Assign(
                targets = [ast.Name(id=retname, ctx=ast.Store())],
                value = node.value
            )
            ret = ast.Return(
                value = ast.Name(id=retname, ctx=ast.Load())
            )
            return [assign, ret]
    vars = internal.find_all_variables(f)
    fprime = ReturnExpander(vars).visit(f)
    f.body = fprime.body
    ast.fix_missing_locations(f)

def canonicalize_variable_names(f: ast.FunctionDef, prefix = 'v') -> None:
    """Modify (in place) the given function definition to give variables canonical names."""
    # first rename everything to a random string followed by a counter
    # then rename them to v0, v1, v2, ...
    tmpname = 'tmp_' + secrets.token_hex(10)
    # set up the mappings
    vars = internal.find_all_variables(f)
    mappings_1stpass = dict()
    mappings_2ndpass = dict()
    for i in range(len(vars)):
        mappings_1stpass[vars[i]] = '{:s}{:d}'.format(tmpname, i)
        mappings_2ndpass[mappings_1stpass[vars[i]]] = '{:s}{:d}'.format(prefix, i)
    # rename to temporary names, then output names
    f_1stpass = internal.rename_variables(f, mappings_1stpass)
    f_2ndpass = internal.rename_variables(f_1stpass, mappings_2ndpass)
    # save results in place
    f.args = f_2ndpass.args
    f.body = f_2ndpass.body
    ast.fix_missing_locations(f)

class FindVariableDependencies(ast.NodeVisitor):
    """Find all the variables a node depends on."""
    def __init__(self):
        self.loads = list()
        self.stores = list()
    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load) and node.id not in self.loads: self.loads.append(node.id)
        if isinstance(node.ctx, ast.Store) and node.id not in self.stores: self.stores.append(node.id)

def contains_name(node: Union[ast.AST, List], name: str) -> bool:
    """Determines whether the given node (or list of nodes) contains a variable with the given name."""
    if isinstance(node, ast.AST): searchin = [node]
    else: searchin = node
    for element in searchin:
        var_deps = FindVariableDependencies()
        var_deps.visit(element)
        if name in var_deps.stores or name in var_deps.loads: return True
    return False

class NameNodeReplacer(ast.NodeTransformer):
    def __init__(self, id, replacement):
        self.id = id
        self.replacement = replacement
    def visit_Name(self, node):
        if node.id == self.id: return self.replacement
        else: return node

def collapse_useless_assigns(f: ast.FunctionDef) -> None:
    """Modify (in place) the given function definition to remove all lines containing tautological/useless assignments. For example, if the code contains a line "x = a" followed by a line "y = x + b", it replaces all subsequent instances of x with a, yielding the single line "y = a + b", up until x is set in another assignment statement.

    Doesn't handle tuples.  Doesn't handle any kind of logic involving if statements or loops."""
    keep_going = True
    while keep_going:
        keep_going = False
        for i in range(len(f.body)):
            stmt = f.body[i]
            if isinstance(stmt, ast.Assign):
                # assignment of the x = a or x = 7
                if isinstance(stmt.targets[0], ast.Name) and (isinstance(stmt.value, ast.Name) or isinstance(stmt.value, ast.Constant)):
                    replacer = NameNodeReplacer(stmt.targets[0].id, stmt.value)
                    # go through all subsequent statements and replace x with a until x is set anew
                    for j in range(i + 1, len(f.body)):
                        stmtprime = f.body[j]
                        if isinstance(stmtprime, ast.Assign):
                            # replace arg with val in the right hand side
                            stmtprime.value = replacer.visit(stmtprime.value)
                            # stop if arg is in the left
                            if contains_name(stmtprime.targets, replacer.id): break
                        else:
                            # replace arg with val in whole statement
                            f.body[j] = replacer.visit(stmtprime)
                    # remove from the body and start over
                    del f.body[i]
                    keep_going = True
                    break
            elif isinstance(stmt, ast.If): raise NotImplementedError("Cannot handle functions with if statements.")
            elif isinstance(stmt, ast.For) or isinstance(stmt, ast.While): raise NotImplementedError("Cannot handle functions with loops.")
    ast.fix_missing_locations(f)
