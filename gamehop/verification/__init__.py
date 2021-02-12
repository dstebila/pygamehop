import ast
import copy
import inspect
import random
import re

from typing import Any, Callable, List, Set, Union
from types import FunctionType

from . import canonicalization
from ..inlining import internal

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
            vardeps = canonicalization.FindVariableDependencies()
            vardeps.visit(stmt.value)
            # find the max level of all variables this statement depends on
            max_level = 0
            for var in vardeps.loads:
                if var in variable_levels:
                    max_level = max(max_level, variable_levels[var])
            # find the variables that are assigned by this statement
            varassigns = canonicalization.FindVariableDependencies()
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
    output: List[ast.stmt] = list()
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

class ReturnVariables(ast.NodeVisitor):
    """Find all the variables that are part of a return statement within this node"""
    def __init__(self):
        self.found = set()
    def visit_Return(self, node):
        if not isinstance(node.value, ast.Name): raise NotImplementedError()
        self.found.add(node.value.id)

class ReverseTaintAnalysisOneLevel(ast.NodeVisitor):
    """Given a set of variables, find all variables that directly depend on these variables"""
    def __init__(self, targets: Set):
        self.targets = targets
        self.found: Set[ast.stmt] = set()
    def visit_Assign(self, node):
        # what variables are assigned by this statement?
        assign_targets = set()
        for t in node.targets:
            assignvars_finder = canonicalization.FindVariableDependencies()
            assignvars_finder.visit(t)
            assign_targets |= set(assignvars_finder.stores)
        # is one of our variables of interest assigned in this statement?
        if not self.targets.isdisjoint(assign_targets):
            # if so, find all the variables in the right hand side and add them to found
            finder = canonicalization.FindVariableDependencies()
            finder.visit(node.value)
            self.found |= set(finder.loads)

def remove_useless_statements(f: ast.FunctionDef):
    """Modify (in place) the given function definition to remove all assign statements that set variables that do not affect the output of the return statement."""
    # find the return variable(s)
    retvars_finder = ReturnVariables()
    retvars_finder.visit(f)
    # find all variables that the return variables depend on
    # each iteration finds one more level of variables that taint the return variables
    # keep iterating until we've found them all
    retvarsdeps_old: Set[Any] = set()
    retvarsdeps_finder = ReverseTaintAnalysisOneLevel(retvars_finder.found)
    retvarsdeps_finder.visit(f)
    retvarsdeps_new = retvarsdeps_finder.targets | retvarsdeps_finder.found
    while retvarsdeps_old != retvarsdeps_new:
        retvarsdeps_old = retvarsdeps_new
        retvarsdeps_finder = ReverseTaintAnalysisOneLevel(retvarsdeps_new)
        retvarsdeps_finder.visit(f)
        retvarsdeps_new = retvarsdeps_finder.targets | retvarsdeps_finder.found
    retvarsdeps = retvarsdeps_new
    # NodeTransformer that will remove all assign statements not assigning to a useful variable
    class RemoveUselessStatements(ast.NodeTransformer):
        def __init__(self, useful_variables: Set):
            self.useful_variables = useful_variables
        def visit_Assign(self, node):
            # what variables are assigned by this statement?
            assign_targets = set()
            for t in node.targets:
                assignvars_finder = canonicalization.FindVariableDependencies()
                assignvars_finder.visit(t)
                assign_targets |= set(assignvars_finder.stores)
            # are all the variables assigned in this statement useless?
            if assign_targets.isdisjoint(self.useful_variables): return []
            else: return node
    fprime = RemoveUselessStatements(retvarsdeps).visit(f)
    f.body = fprime.body
    ast.fix_missing_locations(f)

def canonicalize_function(f: Union[Callable, str]) -> str:
    """Returns a string representing a canonicalized version of the given function.

    It applies the following canonicalizations:
    - return statements only return a single variable or a constant
    - function name is 'f'
    - variable names are 'v0', 'v1', ...
    - lines are reordered based on variable dependencies"""
    # parse the function
    if isinstance(f, FunctionType): t = ast.parse(inspect.getsource(f))
    elif isinstance(f, str): t = ast.parse(f)
    else: raise TypeError()
    # make sure it is a single function
    functionDef = t.body[0]
    assert isinstance(functionDef, ast.FunctionDef)
    # canonicalize return statement
    canonicalization.canonicalize_return(functionDef)
    # canonicalize function name
    canonicalization.canonicalize_function_name(functionDef)
    # canonicalize variables and line numbers and remove useless assignments and statements
    # one pass of canonicalizing variable names allows for canonicalizing the order of
    # lines at the next "level", so we have to repeat until all levels have been canonicalized
    # and the source stops changing; also removing a useless assignment or statement might make
    # another assignment or statement useless, so we keep iterating on those
    # oldstring = None
    # newstring = ast.unparse(ast.fix_missing_locations(t))
    # while oldstring != newstring:
    #     oldstring = newstring
    #     canonicalization.collapse_useless_assigns(functionDef)
    #     remove_useless_statements(functionDef)
    #     canonicalization.canonicalize_variable_names(functionDef)
    #     canonicalize_lineorder(functionDef)
    #     newstring = ast.unparse(ast.fix_missing_locations(t))
    # temporary: don't loop because currently getting an intermediate loop
    canonicalization.collapse_useless_assigns(functionDef)
    remove_useless_statements(functionDef)
    canonicalization.canonicalize_variable_names(functionDef)
    canonicalize_lineorder(functionDef)
    newstring = ast.unparse(ast.fix_missing_locations(t))
    return newstring
