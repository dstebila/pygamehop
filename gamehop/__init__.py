__all__ = ['primitives']

from typing import Any, Callable, List, Set, Union, cast
from gamehop import inlining
from gamehop import verification
from gamehop.primitives import Crypto
import ast
import inspect

def inline(inlinee: Union[Callable, str, ast.FunctionDef], inlinand: Union[Callable, str, ast.FunctionDef, object, ast.ClassDef], arg = '', inline_init = True, search_function_name=None, dest_function_name=None, self_prefix="") -> str:
    inlined = ''
    if type(inlinand) == str:
        inlinand_str = cast(str, inlinand)
        if str.startswith(inlinand_str, 'def'):
            inlined = inlining.inline_function(inlinee, inlinand_str, search_function_name=search_function_name, dest_function_name= dest_function_name, self_prefix=self_prefix)
        elif str.startswith(inlinand_str, 'class'):
            inlined = inlining.inline_class(inlinee, arg, inlinand_str, inline_init = inline_init)
        else:
            raise Exception('String not function or class definition')
    elif type(inlinand) == Callable or type(inlinand) == ast.FunctionDef:
        inlinand_f = cast(Union[Callable, ast.FunctionDef], inlinand)
        inlined = inlining.inline_function(inlinee, inlinand_f, search_function_name=search_function_name, dest_function_name= dest_function_name, self_prefix=self_prefix)
    elif type(inlinand) == ast.ClassDef or type(inlinand) == object or inspect.isclass(inlinand):
        inlinand_class = cast(Union[object, ast.ClassDef], inlinand)
        inlined = inlining.inline_class(inlinee, arg, inlinand_class, inline_init = inline_init)

    r = verification.canonicalize_function(inlined)
    return r

def assertEqual(a: str, b: str, debugging=False):
    if not debugging:
        assert(a == b)
    elif a != b:
        print("Strings differ")
        stringDiff(a,b)
    else:
        print("Strings identical")

def advantage(a: str, b: str, experiment: Crypto.Experiment):
    pass


import difflib

def stringDiff(a,b):
    differences = difflib.ndiff(a.splitlines(keepends=True), b.splitlines(keepends=True))
    diffl = []
    for difference in differences:
        diffl.append(difference)
    print(''.join(diffl), end="\n")
