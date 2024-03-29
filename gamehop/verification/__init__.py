import ast
import copy
import inspect
import random
import re

from typing import Any, Callable, Dict, List, Set, Type, Union
from types import FunctionType

from . import canonicalization
from .. import utils
from .canonicalization import expand
from .canonicalization import simplify
from .canonicalization import ifstatements
from .canonicalization.classes import unnecessary_members

def debug_helper(x, label):
    if False: # change this to True to print some debugging info
        print("======================")
        print("after {:s}".format(label))
        print(ast.unparse(x))

def canonicalize_function(f: Union[Callable, str]) -> str:
    """Returns a string representing a canonicalized version of the given function.

    It applies the following canonicalizations:
    - return statements only return a single variable or a constant
    - function name is 'f'
    - variable names are 'v0', 'v1', ...
    - lines are reordered based on variable dependencies"""
    # parse the function
    functionDef = utils.get_function_def(f)
    assert isinstance(functionDef, ast.FunctionDef)
    str_previous = ""
    str_current = ast.unparse(ast.fix_missing_locations(functionDef))
    while str_previous != str_current:
        str_previous = str_current
        # Inline lambdas first so that the inlined expression will be expanded later
        canonicalization.inline_lambdas(functionDef)
        debug_helper(functionDef, "canonicalization.inline_lambdas")
        ifstatements.if_statements_to_expressions(functionDef)
        debug_helper(functionDef, "ifstatements.if_statements_to_expressions")
        expand.expand_non_compact_expressions(functionDef)
        debug_helper(functionDef, "expand.expand_non_compact_expressions")
        # canonicalize function name
        canonicalization.canonicalize_function_name(functionDef)
        debug_helper(functionDef, "canonicalization.canonicalize_function_name")
        canonicalization.collapse_useless_assigns(functionDef)
        debug_helper(functionDef, "canonicalization.collapse_useless_assigns")
        canonicalization.simplify.simplify(functionDef)
        debug_helper(functionDef, "canonicalization.simplify.simplify")
        canonicalization.canonicalize_line_order(functionDef)
        debug_helper(functionDef, "canonicalization.canonicalize_line_order")
        canonicalization.canonicalize_argument_order(functionDef)
        debug_helper(functionDef, "canonicalization.canonicalize_argument_order")
        canonicalization.canonicalize_variable_names(functionDef)
        debug_helper(functionDef, "canonicalization.canonicalize_variable_names")
        str_current = ast.unparse(ast.fix_missing_locations(functionDef))
    return str_current

def canonicalize_game(c: Union[Type[Any], str, ast.ClassDef]) -> str:
    cdef = utils.get_class_def(c)
    cdef.name = "G"
    str_previous = ""
    str_current = ast.unparse(ast.fix_missing_locations(cdef))
    while str_previous != str_current:
        str_previous = str_current
        # determine which members are used within each function, so that we can pass that
        # list of dependencies to canonicalize_line_order
        members_in_scope: Dict[str, List[str]] = dict()
        for f in cdef.body:
            if not isinstance(f, ast.FunctionDef):
                raise ValueError(f"Cannot canonicalize games containing anything other than functions; {cdef.name} contains a node of type {type(f).__name__}")
            selfname = f.args.args[0].arg
            members_in_scope[selfname + "." + f.name] = list()
            for v in utils.vars_depends_on(f):
                if v.startswith(selfname + "."):
                    members_in_scope[selfname + "." + f.name].append(v)
        for i, f in enumerate(cdef.body):
            if not isinstance(f, ast.FunctionDef):
                raise ValueError(f"Cannot canonicalize games containing anything other than functions; {cdef.name} contains a node of type {type(f).__name__}")
            ifstatements.if_statements_to_expressions(f)
            debug_helper(f, "ifstatements.if_statements_to_expressions")
            expand.expand_non_compact_expressions(f)
            debug_helper(f, "expand.expand_non_compact_expressions")
            canonicalization.collapse_useless_assigns(f)
            debug_helper(f, "canonicalization.collapse_useless_assigns")
            canonicalization.simplify.simplify(f)
            debug_helper(f, "canonicalization.simplify.simplify")
            if f.name != "__init__":
                canonicalization.canonicalize_line_order(f, members_in_scope)
                debug_helper(f, "canonicalization.canonicalize_line_order")
            canonicalization.canonicalize_variable_names(f)
            debug_helper(f, "canonicalization.canonicalize_variable_names")
            cdef.body[i] = f
        unnecessary_members(cdef)
        debug_helper(cdef, "canonicalization.classes.unnecessary_members")
        str_current = ast.unparse(ast.fix_missing_locations(cdef))
    return ast.unparse(ast.fix_missing_locations(cdef))
