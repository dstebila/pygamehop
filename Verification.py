import ast
import copy
import inspect
import random
import re

from typing import Callable, List, Union

def findallvariables(fdef: ast.FunctionDef) -> List[str]:
    """Return a list of all variables in the function, including function parameters."""
    vars = list()
    # function arguments
    args = fdef.args
    if len(args.posonlyargs) > 0: raise NotImplementedError()
    if len(args.kwonlyargs) > 0: raise NotImplementedError()
    if len(args.kw_defaults) > 0: raise NotImplementedError()
    if len(args.defaults) > 0: raise NotImplementedError()
    for arg in args.args:
        vars.append(arg.arg)
    # find all assigned variables
    for stmt in fdef.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    if target.id not in vars: vars.append(target.id)
                elif isinstance(target, ast.Tuple) or isinstance(target, ast.List):
                    for elt in target.elts:
                        if elt.id not in vars: vars.append(elt.id)
                else: raise NotImplementedError()
    return vars

class NameRenamer(ast.NodeTransformer):
    """Replaces ids in Name nodes based on the provided mapping."""
    def __init__(self, mapping):
        self.mapping = mapping
    def visit_Name(self, node):
        if node.id in self.mapping: return ast.Name(id=self.mapping[node.id], ctx=node.ctx)
        else: return node

def renamevariables(fdef: ast.FunctionDef, mapping: dict) -> ast.FunctionDef:
    """Returns a copy of the function definition node with all the variables in the given function definition renamed based on the provided mapping."""
    retvalue = copy.deepcopy(fdef)
    for arg in retvalue.args.args:
        if arg.arg in mapping: arg.arg = mapping[arg.arg]
    newbody = list()
    for stmt in retvalue.body:
        newbody.append(NameRenamer(mapping).visit(stmt))
    retvalue.body = newbody
    return retvalue

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
    vars = findallvariables(f)
    fprime = ReturnExpander(vars).visit(f)
    f.body = fprime.body
    ast.fix_missing_locations(f)

def canonicalize_functionname(f: ast.FunctionDef, name = 'f') -> None:
    """Modify (in place) the given function definition to have a canonical name."""
    f.name = name
    ast.fix_missing_locations(f)

def canonicalize_variablenames(f: ast.FunctionDef, prefix = 'v') -> None:
    """Modify (in place) the given function definition to give variables canonical names."""
    # first rename everything to a random string followed by a counter
    # then rename them to v0, v1, v2, ...
    tmpname = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r' ,'s', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    random.shuffle(tmpname)
    tmpname = ''.join(tmpname)
    # set up the mappings
    vars = findallvariables(f)
    mappings_1stpass = dict()
    mappings_2ndpass = dict()
    for i in range(len(vars)):
        mappings_1stpass[vars[i]] = '{:s}{:d}'.format(tmpname, i)
        mappings_2ndpass[mappings_1stpass[vars[i]]] = '{:s}{:d}'.format(prefix, i)
    # rename to temporary names, then output names
    f_1stpass = renamevariables(f, mappings_1stpass)
    f_2ndpass = renamevariables(f_1stpass, mappings_2ndpass)
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

def canonicalize_lineorder(f: ast.FunctionDef) -> None:
    """Modify (in place) the given function definition so that its lines are in a canonical order.
    
    The idea of the canonicalization is as follows.  Each line is to be assigned a "level" based on how deep it is in the variable dependency tree.  All lines at level i are independent of each other, and are dependent on a variable assigned in level i-1.  For each level, sort the lines based on the string representation of their right-hand side.
    
    This algorithm is very limited for now.  It assumes:
    - the function consists solely of assignment and return statements
    - functions have no side effects, and in particular do not modify their inputs"""
    line_levels = dict()
    variable_levels = dict()
    # level of all function arguments is 0
    for arg in f.args.args:
        variable_levels[arg.arg] = 0
    for stmt in f.body:
        if isinstance(stmt, ast.Assign):
            # find all the variables this statement depends on
            vardeps = FindVariableDependencies()
            vardeps.visit(stmt.value)
            # find the max level of all variables this statement depends on
            max_level = 0
            for var in vardeps.loads:
                if var in variable_levels:
                    max_level = max(max_level, variable_levels[var])
            # find the variables that are assigned by this statement
            varassigns = FindVariableDependencies()
            if len(stmt.targets) != 1: raise NotImplementedError
            varassigns.visit(stmt.targets[0])
            # set the level of the variables assigned by this statement
            for var in varassigns.stores: variable_levels[var] = max_level + 1
            # store the level of this statement
            # print('[level: {:d}] {:s}'.format(max_level + 1, ast.unparse(stmt)))
            line_levels[stmt] = max_level + 1
        elif isinstance(stmt, ast.Return):
            returnstmt = stmt
        else: raise NotImplementedError()
    # get all the levels computed
    levels = list(set(line_levels.values()))
    levels.sort()
    # start building the sorted lines
    output = list()
    for level in levels:
        # find the lines at this level
        lines_at_this_level = list()
        for line in line_levels:
            if line_levels[line] == level: lines_at_this_level.append(line)
        # sort the lines by the text representation of their right hand side
        lines_at_this_level.sort(key = lambda stmt: ast.unparse(stmt.value))
        # uncomment the following line for debugging to get level information embedded in the program
        # output.append(ast.Assign(targets=[ast.Name(id='level', ctx=ast.Store())],value=ast.Constant(value='level {:d}'.format(level))))
        # add these lines to the output
        output.extend(lines_at_this_level)
    # don't forget to include the return statement
    output.append(returnstmt)
    # set the new function body
    f.body = output
    ast.fix_missing_locations(f)

def canonicalize_function(f: Union[Callable, str]) -> str:
    """Returns a string representing a canonicalized version of the given function.
    
    It applies the following canonicalizations:
    - return statements only return a single variable or a constant
    - function name is 'f'
    - variable names are 'v0', 'v1', ...
    - lines are reordered based on variable dependencies"""
    # parse the function
    if isinstance(f, Callable): t = ast.parse(inspect.getsource(f))
    elif isinstance(f, str): t = ast.parse(f)
    else: raise TypeError()
    # make sure it is a single function
    functionDef = t.body[0]
    assert isinstance(functionDef, ast.FunctionDef)
    # canonicalize return statement
    canonicalize_return(functionDef)
    # canonicalize function name
    canonicalize_functionname(functionDef)
    # canonicalize variables and line numbers
    # one pass of canonicalizing variable names allows for canonicalizing the order of
    # lines at the next "level", so we have to repeat until all levels have been canonicalized
    # and the source stops changing
    oldstring = None
    newstring = ast.unparse(ast.fix_missing_locations(t))
    while oldstring != newstring:
        oldstring = newstring
        canonicalize_variablenames(functionDef)
        canonicalize_lineorder(functionDef)
        newstring = ast.unparse(ast.fix_missing_locations(t))
    return newstring

def inline_function(fdest: Callable, farg: Callable):
    """Returns a string representing the second function inlined into the first.
    
    Only works on calls to the function in an Assign statement."""
    # parse the functions
    tdest = ast.parse(inspect.getsource(fdest))
    targ = ast.parse(inspect.getsource(farg))
    # get the function definitions
    fdest_def = tdest.body[0]
    assert isinstance(fdest_def, ast.FunctionDef)
    farg_def = targ.body[0]
    assert isinstance(farg_def, ast.FunctionDef)
    # define the inliner which will do the replacements
    class Inliner(ast.NodeTransformer):
        def __init__(self, farg_def):
            self.farg_def = farg_def
            self.replacement_count = 0
        def visit_Assign(self, stmt):
            if isinstance(stmt.value, ast.Call) and stmt.value.func.id == self.farg_def.name:
                self.replacement_count += 1
                # prefix all variables in inlinand
                vars = findallvariables(self.farg_def)
                mappings = dict()
                for var in vars: mappings[var] = 'v_{:s}_{:d}_{:s}'.format(self.farg_def.name, self.replacement_count, var)
                newfarg_def = renamevariables(farg_def, mappings)
                # map the parameters onto the arguments
                assert len(stmt.value.args) == len(newfarg_def.args.args)
                mappings = dict()
                for i in range(len(stmt.value.args)):
                    mappings[newfarg_def.args.args[i].arg] = stmt.value.args[i].id
                newfarg_def = renamevariables(newfarg_def, mappings)
                # turn the final return statement into an assignment
                assert isinstance(newfarg_def.body[-1], ast.Return)
                newret = ast.Assign(targets=stmt.targets, value=newfarg_def.body[-1].value)
                newfarg_def.body[-1] = newret
                # output is the inlined function body
                return newfarg_def.body
            else: return stmt
    # run the inliner
    newfdest_def = Inliner(farg_def).visit(fdest_def)
    return ast.unparse(ast.fix_missing_locations(newfdest_def))
