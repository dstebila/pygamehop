import ast
import copy
import inspect
import random
import re

from typing import Any, Callable, List, Set, Union
from types import FunctionType

from . import canonicalization
from ..inlining import internal

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
    canonicalization.collapse_useless_assigns(functionDef)
    canonicalization.canonicalize_line_order(functionDef)
    canonicalization.canonicalize_argument_order(functionDef)
    canonicalization.canonicalize_variable_names(functionDef)
    newstring = ast.unparse(ast.fix_missing_locations(t))
    return newstring
