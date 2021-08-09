import ast
import copy
import inspect
import random
import re

from typing import Any, Callable, List, Set, Union
from types import FunctionType

from . import canonicalization
from ..inlining import internal
from .canonicalization import expand
from .canonicalization import simplify
from .canonicalization import ifstatements

def debug_helper(functionDef, label):
    if False: # change this to True to print some debugging info
        print("======================")
        print("after {:s}".format(label))
        print(ast.unparse(functionDef))

def canonicalize_function(f: Union[Callable, str]) -> str:
    """Returns a string representing a canonicalized version of the given function.

    It applies the following canonicalizations:
    - return statements only return a single variable or a constant
    - function name is 'f'
    - variable names are 'v0', 'v1', ...
    - lines are reordered based on variable dependencies"""
    # parse the function
    functionDef = internal.get_function_def(f)
    assert isinstance(functionDef, ast.FunctionDef)
    str_previous = ""
    str_current = ast.unparse(ast.fix_missing_locations(functionDef))
    while str_previous != str_current:
        str_previous = str_current
        ifstatements.if_statements_to_expressions(functionDef)
        debug_helper(functionDef, "ifstatements.if_statements_to_expressions")
        expand.call_arguments(functionDef)
        debug_helper(functionDef, "expand.call_arguments")
        # canonicalize return statement
        canonicalization.canonicalize_return(functionDef)
        debug_helper(functionDef, "canonicalization.canonicalize_return")
        # canonicalize function name
        canonicalization.canonicalize_function_name(functionDef)
        debug_helper(functionDef, "canonicalization.canonicalize_function_name")
        canonicalization.inline_lambdas(functionDef)
        debug_helper(functionDef, "canonicalization.inline_lambdas")
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
