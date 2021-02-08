__all__ = ['primitives']

from typing import Any, Callable, List, Set, Union
import gamehop.inlining
import gamehop.verification
import ast
import inspect

def inline(inlinee: Union[Callable, str, ast.FunctionDef], inlinand: Union[Callable, str, ast.FunctionDef, object, ast.ClassDef], arg = '', inline_init = True, search_function_name=None, dest_function_name=None, self_prefix="") -> str:
    inlined = ''
    if type(inlinand) == str:
        if str.startswith(inlinand, 'def'):
            inlined = inlining.inline_function(inlinee, inlinand, search_function_name=search_function_name, dest_function_name= dest_function_name, self_prefix=self_prefix)
        elif str.startswith(inlinand, 'class'):
            inlined = inlining.inline_class(inlinee, arg, inlinand, inline_init = inline_init)
        else:
            raise error('String not function or class definition')
    elif type(inlinand) == Callable or type(inlinand) == ast.FunctionDef:
        inlined = inlining.inline_function(inlinee, inlinand, search_function_name=search_function_name, dest_function_name= dest_function_name, self_prefix=self_prefix)
    elif type(inlinand) == ast.ClassDef or type(inlinand) == object or inspect.isclass(inlinand):
        inlined = inlining.inline_class(inlinee, arg, inlinand, inline_init = inline_init)

    r = verification.canonicalize_function(inlined)
    return r

def assertEqual(a: str, b: str, debugging=False):
    if not debugging:
        assert(a == b)
    elif a != b:
        print("Strings differ")
        stringDiff(a,b)
    else:
        prints("Strings identical")

def advantage(a: str, b: str, scheme, experiment):
    pass


import difflib

def stringDiff(a,b):
    differences = difflib.ndiff(a.splitlines(keepends=True), b.splitlines(keepends=True))
    diffl = []
    for difference in differences:
        diffl.append(difference)
    print(''.join(diffl), end="\n")
