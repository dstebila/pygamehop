import ast
import copy
import inspect
import random
import re

from typing import Any, Callable, List, Set, Union

from . import canonicalization
from ..inlining import internal

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

def collapse_useless_assigns(f: ast.FunctionDef):
    """Modify (in place) the given function definition to remove all lines containing tautological/useless assignments. For example, if the code contains a line "x = a" followed by a line "y = x + b", it replaces all subsequent instances of x with a, yielding the single line "y = a + b", up until x is set in another assignment statement.

    Doesn't handle tuples.  Doesn't handle any kind of logic involving if statements or loops."""
    # keep looping until we don't remove any statements within a loop of the execution
    keep_going = True
    while keep_going:
        keep_going = False
        # let's start at the very beginning, a very good place to start
        for i in range(len(f.body)):
            stmt = f.body[i]
            # if the statement is an assignment of a single variable to another variable, e.g., x = a
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name) and isinstance(stmt.value, ast.Name):
                arg = stmt.targets[0].id
                val = stmt.value.id
                # go through all subsequent statements and replace x with a until x is set anew
                for j in range(i + 1, len(f.body)):
                    stmtprime = f.body[j]
                    if isinstance(stmtprime, ast.Assign):
                        # replace arg with val in the right hand side
                        stmtprime.value = NameRenamer({arg: val}).visit(stmtprime.value)
                        # stop if arg is in the left
                        if contains_name(stmtprime.targets, arg): break
                    else:
                        # replace arg with val in whole statement
                        f.body[j] = NameRenamer({arg, val}).visit(stmtprime)
                # remove from the body and start over
                del f.body[i]
                keep_going = True
                break

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
        self.found = set()
    def visit_Assign(self, node):
        # what variables are assigned by this statement?
        assign_targets = set()
        for t in node.targets:
            assignvars_finder = FindVariableDependencies()
            assignvars_finder.visit(t)
            assign_targets |= set(assignvars_finder.stores)
        # is one of our variables of interest assigned in this statement?
        if not self.targets.isdisjoint(assign_targets):
            # if so, find all the variables in the right hand side and add them to found
            finder = FindVariableDependencies()
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
    retvarsdeps_old = set()
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
                assignvars_finder = FindVariableDependencies()
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
    if isinstance(f, Callable): t = ast.parse(inspect.getsource(f))
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
    #     collapse_useless_assigns(functionDef)
    #     remove_useless_statements(functionDef)
    #     canonicalization.canonicalize_variable_names(functionDef)
    #     canonicalize_lineorder(functionDef)
    #     newstring = ast.unparse(ast.fix_missing_locations(t))
    # temporary: don't loop because currently getting an intermediate loop
    collapse_useless_assigns(functionDef)
    remove_useless_statements(functionDef)
    canonicalization.canonicalize_variable_names(functionDef)
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
                vars = internal.find_all_variables(self.farg_def)
                mappings = dict()
                for var in vars: mappings[var] = 'v_{:s}_{:d}_{:s}'.format(self.farg_def.name, self.replacement_count, var)
                newfarg_def = internal.rename_variables(farg_def, mappings)
                # map the parameters onto the arguments
                assert len(stmt.value.args) == len(newfarg_def.args.args)
                mappings = dict()
                for i in range(len(stmt.value.args)):
                    mappings[newfarg_def.args.args[i].arg] = stmt.value.args[i].id
                newfarg_def = internal.rename_variables(newfarg_def, mappings)
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

class ConstantReplacer(ast.NodeTransformer):
    """Replaces a Name node with a constant value."""
    def __init__(self, id, val):
        self.id = id
        self.val = val
    def visit_Name(self, node):
        if node.id == self.id:
            if isinstance(node.ctx, ast.Load): return ast.Constant(value=self.val)
            elif isinstance(node.ctx, ast.Store): raise NotImplementedError()
        else: return node

class AttributeInliner(ast.NodeTransformer):
    """Replaces basename.whatever with formatstring.format(whatever)."""
    def __init__(self, basename: str, formatstring: str):
        self.basename = basename
        self.formatstring = formatstring
    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name) and node.value.id == self.basename:
            return ast.Name(id=self.formatstring.format(node.attr), ctx=node.ctx)
        elif isinstance(node.value, ast.Attribute):
            node.value = self.visit_Attribute(node.value)
            return node
        else: return node

# expands the Inliner class inside inline_function above; those two could probably be unified somehow
class ClassInliner(ast.NodeTransformer):
    def __init__(self, inlinand_name, inlinand_value, selfformatstring):
        self.inlinand_name = inlinand_name
        self.inlinand_value = inlinand_value
        self.selfformatstring = selfformatstring
        self.replacement_count = 0
    def visit_Assign(self, stmt):
        # is this assign a call to the thing we're supposed to replace?
        if isinstance(stmt.value, ast.Call) and isinstance(stmt.value.func, ast.Attribute) and         stmt.value.func.value.id == self.inlinand_name:
            # get the ClassDef of the class we're inlining
            inlinand_classdef = ast.parse(inspect.getsource(self.inlinand_value)).body[0]
            assert isinstance(inlinand_classdef, ast.ClassDef)
            # find the method that we're supposed to inline
            methoddef = None
            for member in inlinand_classdef.body:
                if not isinstance(member, ast.FunctionDef): raise NotImplementedError()
                if member.name == stmt.value.func.attr:
                    methoddef = member
                    break
            if methoddef == None: raise LookupError()
            self.replacement_count += 1
            # prefix all variables in inlinand
            vars = internal.find_all_variables(methoddef)
            mappings = dict()
            for var in vars: mappings[var] = 'v_{:s}_{:s}_{:d}_{:s}'.format(self.inlinand_name, methoddef.name, self.replacement_count, var)
            newmethoddef = internal.rename_variables(methoddef, mappings)
            selfmapped = mappings[methoddef.args.args[0].arg]
            # map the parameters onto the arguments
            assert len(stmt.value.args) == len(methoddef.args.args) - 1 # offset by 1 due to self
            mappings = dict()
            for i in range(len(stmt.value.args)):
                mappings[newmethoddef.args.args[i + 1].arg] = stmt.value.args[i].id
            newmethoddef = internal.rename_variables(newmethoddef, mappings)
            # turn the final return statement into an assignment
            assert isinstance(newmethoddef.body[-1], ast.Return)
            newret = ast.Assign(targets=stmt.targets, value=newmethoddef.body[-1].value)
            newmethoddef.body[-1] = newret
            # inline self.whatever
            newmethoddef = AttributeInliner(selfmapped, self.selfformatstring).visit(newmethoddef)
            # output is the inlined function body
            return newmethoddef.body
        else: return stmt

def inline_argument(f: Union[Callable, str], arg: str, val: Any):
    """Returns a string representing the provided function with the given argument inlined to the given value.  Works on integers, strings, and classes."""
    # parse the function
    if isinstance(f, Callable): t = ast.parse(inspect.getsource(f))
    elif isinstance(f, str): t = ast.parse(f)
    else: raise TypeError()
    # get the function definition
    fdef = t.body[0]
    assert isinstance(fdef, ast.FunctionDef)
    # find out what type of argument we're supposed to be replacing
    typeofarg = None
    for a in fdef.args.args:
        if a.arg == arg:
            typeofarg = a.annotation.id
            break
    # didn't find it
    if typeofarg == None: raise LookupError()
    # replace constants like integers or strings
    if typeofarg == 'int' or typeofarg == 'str':
        newfdef = ConstantReplacer(arg, val).visit(fdef)
    # replace class methods
    # elif typeofarg == val.__name__: ## TODO: FIXME: the old line of code doesn't work with the generics approach yet
    elif True:
        selfformatstring = 'v_{:s}_self_'.format(arg) + '{:s}'
        newfdef = ClassInliner(arg, val, selfformatstring).visit(fdef)
        # need to take unresolved arguments from the inlinand __init__ and make them arguments of the newfdef
        inlinand_classdef = ast.parse(inspect.getsource(val)).body[0]
        for s in inlinand_classdef.body:
            if isinstance(s, ast.FunctionDef) and s.name == '__init__':
                for init_arg in range(1, len(s.args.args)):
                    newfdef.args.args.append(s.args.args[init_arg])
                # need to take the body of the __init__ of the inlinand and put it at the start of the newfdef body
                initprime = AttributeInliner(s.args.args[0].arg, selfformatstring).visit(s)
                initprime.body.extend(newfdef.body)
                newfdef.body = initprime.body
    # unrecognized type
    else: raise NotImplementedError('type of argument: {:s}, class of value: {:s}'.format(typeofarg, val.__name__))
    # remove the argument from the arguments list
    for a in newfdef.args.args:
        if a.arg == arg:
            newfdef.args.args.remove(a)
            break
    # return the resulting function
    return ast.unparse(ast.fix_missing_locations(newfdef))


import difflib

def stringDiff(a,b):
    differences = difflib.ndiff(a.splitlines(keepends=True), b.splitlines(keepends=True))
    diffl = []
    for difference in differences:
        diffl.append(difference)
    print(''.join(diffl), end="\n")
