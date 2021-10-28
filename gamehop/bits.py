import ast
from typing import Union, List, TypeVar

T = TypeVar('T')
def ensure_list(thing: Union[T, List[T]]) -> List[T]:
    ''' Argument is wrapped in a list() if it is not already a list'''
    if isinstance(thing, list):
        return thing
    else:
        return [ thing ]

def glue_list_and_vals(vals: List[Union[T, List[T], None]]) -> List[T]:
    ''' Create a single list out of vals.  If a val is a list, then it's
    contents are added to the list, otherwise the val itself is added.
    Any None values are removed.'''
    ret_val: List[T] = list()
    for v in vals:
        if isinstance(v, list):
            ret_val.extend(v)
        elif v is None:
            continue
        else:
            ret_val.append(v)
    return ret_val

def append_if_unique(l, val):
    if not val in l:
        l.append(val)

def unique_elements(l: List[T]) -> List[T]:
    ''' Returns a list where elements are taken from the given list, but only the first occurance of 
    any particular element is kept.  Subsequent occurances of each element are removed.
    '''
    ret = list()
    for v in l:
        if v not in ret:
            ret.append(v)
    return ret


def attribute_fqn(node: ast.expr) -> List[str]:
    '''From an attribute node, determine the full name, given as a list of strings.  Handles
    attributes of attributes etc. recursively.
    Note that the outer Attribute represents the rightmost name in a full name of an attribute, i.e.
    for a.b.c, the outer Attribute node represents 'c' and the innermost node is a Name with id 'a'.

    '''
    fqn: List[str] = [ ]
    if isinstance(node, ast.Attribute):
        val = node.value
        fqn.insert(0, node.attr)
        # Keep on adding prefixes (object names) to the varname until we are at the outer name
        while isinstance(val, ast.Attribute):
            fqn.insert(0, val.attr)
            val = val.value

    # At the outer name
    if isinstance(val, ast.Name):
        fqn.insert(0, val.id)
    elif isinstance(val, ast.arg):
        fqn.insert(0, val.arg)
    else:
        # Not sure what else will come up!
        assert(False)
    
    return fqn

def fqn_str(fqn: List[str]) -> str:
    return ".".join(fqn)

def str_fqn(varname: str) -> List[str]:
    return varname.split('.')

def called_function_name(node: ast.Call):
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return ".".join(attribute_fqn(node.func))
    # Don't know what else might come up!
    assert(False)
