import ast
import inspect
import random
import re

from typing import Callable

class RenameVariables(ast.NodeTransformer):
    def __init__(self, mappings):
        self.mappings = mappings
    def visit_Name(self, node):
        if node.id in self.mappings: return ast.Name(id=self.mappings[node.id], ctx=node.ctx)
        else: return node

def canonicalize_return(f: ast.FunctionDef) -> None:
    class ReturnExpander(ast.NodeTransformer):
        def __init__(self):
            self.variables = set()
        def visit_Name(self, node):
            self.variables.add(node.id)
            return node
        def visit_Return(self, node):
            i = 0
            while 'myreturnvariable{:d}'.format(i) in self.variables: i += 1
            # if it directly returns a constant or variable, consider that canonical
            if isinstance(node.value, ast.Constant): return node
            if isinstance(node.value, ast.Name): return node
            # otherwise, make a new assignment for that return value and then return the newly assigned variable
            assign = ast.Assign(
                targets = [ast.Name(id='myreturnvariable{:d}'.format(i), ctx=ast.Store())],
                value = node.value
            )
            ret = ast.Return(
                value = ast.Name(id='myreturnvariable{:d}'.format(i), ctx=ast.Load())
            )
            return [assign, ret]
    fprime = ReturnExpander().visit(f)
    f.body = fprime.body
    ast.fix_missing_locations(f)

def canonicalize_functionname(f: ast.FunctionDef) -> None:
    f.name = "f"
    ast.fix_missing_locations(f)

def canonicalize_variablenames(f: ast.FunctionDef) -> None:
    # first rename everything to a random string followed by a counter
    # then rename them to v0, v1, v2, ...
    mappings_tmp = dict()
    mappings = dict()
    tmpname = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r' ,'s', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    random.shuffle(tmpname)
    tmpname = ''.join(tmpname)
    # canonicalize arguments in the given order
    args = f.args
    if len(args.posonlyargs) > 0: raise NotImplementedError()
    if len(args.kwonlyargs) > 0: raise NotImplementedError()
    if len(args.kw_defaults) > 0: raise NotImplementedError()
    if len(args.defaults) > 0: raise NotImplementedError()
    for arg in args.args:
        mappings_tmp[arg.arg] = "{:s}{:d}".format(tmpname, len(mappings))
        mappings[mappings_tmp[arg.arg]] = "v{:d}".format(len(mappings))
        arg.arg = mappings[mappings_tmp[arg.arg]]
    # find all assigned variables
    for stmt in f.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    if target.id not in mappings_tmp: 
                        mappings_tmp[target.id] = "{:s}{:d}".format(tmpname, len(mappings))
                        mappings[mappings_tmp[target.id]] = "v{:d}".format(len(mappings))
                elif isinstance(target, ast.Tuple) or isinstance(target, ast.List):
                    for elt in target.elts:
                        if elt.id not in mappings_tmp: 
                            mappings_tmp[elt.id] = "{:s}{:d}".format(tmpname, len(mappings))
                            mappings[mappings_tmp[elt.id]] = "v{:d}".format(len(mappings))
                else: raise NotImplementedError()
    # rename all variables per the mapping
    fprime = RenameVariables(mappings_tmp).visit(f)
    fprime = RenameVariables(mappings).visit(fprime)
    f.body = fprime.body
    ast.fix_missing_locations(f)

class FindVariableDependencies(ast.NodeVisitor):
    def __init__(self):
        self.loads = list()
        self.stores = list()
    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load) and node.id not in self.loads: self.loads.append(node.id)
        if isinstance(node.ctx, ast.Store) and node.id not in self.stores: self.stores.append(node.id)

def canonicalize_lineorder(f: ast.FunctionDef) -> None:
    # find the level of every line
    # algorithm idea:
    # 1. The level of a line is 1 more than the max level of (the level of the last line where each variable the line in question depends on)
    # 2. Determine the level of each line, and put it in a list of lines for that level
    # 3. For each level, sort the lines based on the string representation of their right hand side
    # 4. Return the lines in order by level
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

def canonicalize(f: Callable) -> str:
    t = ast.parse(inspect.getsource(f))
    functionDef = t.body[0]
    assert isinstance(functionDef, ast.FunctionDef)
    canonicalize_return(functionDef)
    canonicalize_functionname(functionDef)
    canonicalize_variablenames(functionDef)
    canonicalize_lineorder(functionDef)
    canonicalize_variablenames(functionDef)
    return ast.unparse(ast.fix_missing_locations(t))
