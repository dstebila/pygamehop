import ast
import copy
import difflib
import inspect
import types
from typing import Any, Callable, Dict, List, Optional, Type, Union, TypeVar
from typing import _GenericAlias # type: ignore

from . import node_traverser as nt

def stringDiff(a,b):
    differences = difflib.ndiff(a.splitlines(keepends=True), b.splitlines(keepends=True))
    diffl = []
    for difference in differences:
        diffl.append(difference)
    print(''.join(diffl), end="\n")

class NewNodeVisitor(ast.NodeVisitor):
    """Adds the ability to handle List[ast.stmt] to ast.NodeVistor"""
    def __init__(self, node=None):
        if node is not None:
            self.visit(node)

    def visit(self, node):
        if isinstance(node, list):
            newnode = ast.Module()
            newnode.body = node
            super().visit(newnode)
        else:
            super().visit(node)

S = TypeVar('S', bound=ast.AST)
def rename_variables(node: S, mapping: dict, error_if_exists = True) -> S:
    for n in nt.nodes(node, nodetype = ast.Name):
        assert(isinstance(n, ast.Name))
        if error_if_exists and (n.id in mapping.values()):
            raise ValueError("New name '{:s}' already exists in function".format(n.id))
        if n.id in mapping:
            n.id = mapping[n.id]
    return node

def rename_function_body_variables(f: ast.FunctionDef, mapping: dict, error_if_exists = True) -> ast.FunctionDef:
    """Modifies, in place, all the variables in the given function definition renamed based on the provided mapping.  Raises a ValueError if the new name is already used in the function."""
    f = rename_variables(f, mapping, error_if_exists)

    # rename any relevant function parameters
    for arg in f.args.args:
        if error_if_exists and (arg.arg in mapping.values()):
            raise ValueError("New name '{:s}' already exists in function".format(arg.arg))
        if arg.arg in mapping:
            arg.arg = mapping[arg.arg]
    return f

class NamePrefixer(nt.NodeTraverser):
    def __init__(self, prefix: str):
        self.prefix = prefix
        self.stored_vars: List[str] = list()
        super().__init__()

    def visit_Name(self, node: ast.Name) -> ast.Name:
        # rename new stored variables, and remember that we did so
        if isinstance(node.ctx, ast.Store):
            self.stored_vars.append(node.id)
            node.id = self.prefix + node.id

        # rename loaded variables only if we have already renamed when they were stored
        # otherwise we are loading from something defined outside our current view
        if isinstance(node.ctx, ast.Load):
            if node.id in self.stored_vars:
                node.id = self.prefix + node.id
        return node

def prefix_names(node, prefix):
    return NamePrefixer(prefix).visit_statements(node)

class NameNodeReplacer(nt.NodeTraverser):
    """Replaces all instances of a Name node with a given node, for each name in the given dictionary of replacements."""
    def __init__(self, replacements: Dict[str, ast.expr]):
        self.replacements = replacements
        super().__init__()
    def visit_Name(self, node):
        if node.id in self.replacements: 
            if isinstance(self.replacements[node.id], str):
                return ast.Name(id=self.replacements[node.id], ctx=node.ctx)
            else: return self.replacements[node.id]
        else: return node

class AttributeNodeReplacer(nt.NodeTraverser):
    """Replaces all instances of an Attribute node (possibly multiple attributes deep) with a Name node with the given name."""
    def __init__(self, needle: List[str], replacement: str):
        self.needle = needle
        self.replacement = replacement
        super().__init__()
    def visit_Attribute(self, node):
        name = ast.unparse(node)
        needle = ".".join(self.needle)
        if needle.endswith("*"):
            if name.startswith(needle[:-1]): return ast.Name(id=self.replacement + name[len(needle)-1:], ctx=node.ctx)
        else:
            if name == needle: return ast.Name(id=self.replacement, ctx=node.ctx)
            if name.startswith(needle + "."): return ast.Name(id=self.replacement + name[len(needle):], ctx=node.ctx)
        if name.startswith(needle):
            return ast.Name(id=self.replacement, ctx=node.ctx)
        return node

def stored_vars(node):
    # TODO: this is probably not what we want if there are inner scopes.
    return [ n.id for n in nt.nodes(node, nodetype = ast.Name) if isinstance(n.ctx, ast.Store) ]

def vars_depends_on(node: Optional[ast.AST]) -> List[str]:
    # TODO: this is not correct if there are any inner scopes where the names
    # are redefined
    if node is None: return list()

    def node_deps(node):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            return node.id
        if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
            return node_deps(node.value) + "." + node.attr
        if isinstance(node, ast.arg):
            return node.arg
        return None

    return nt.bits.glue_list_and_vals([ node_deps(n) for n in nt.nodes(node) ])

def vars_assigns_to(node: Union[ast.AST, List[ast.stmt]]) -> List[str]:
    # TODO: this is not correct if assign happens in an inner scope
    # TODO: when fixing above, think about global and nonlocal keywords
    def node_assigns(node):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            return node.id
        if isinstance(node, ast.Attribute):
            if isinstance(node.ctx, ast.Store):
                return vars_depends_on(node.value)
        return None

    return nt.bits.glue_list_and_vals([ node_assigns(n) for n in nt.nodes(node) ])

def remove_indentation(src: str) -> str:
    indentation = 0
    while src[indentation] == ' ' or src[indentation] == "\t": indentation += 1
    newsrc = []
    for line in src.splitlines():
        newsrc.append(line[indentation:])
    return "\n".join(newsrc)

def get_function_def(f: Union[Callable, str, ast.FunctionDef]) -> ast.FunctionDef:
    """Gets the ast.FunctionDef for a function that is given as a function or as a string."""
    # parse the function
    if isinstance(f, types.FunctionType): t = ast.parse(remove_indentation(inspect.getsource(f)))
    elif isinstance(f, str): t = ast.parse(remove_indentation(f))
    elif isinstance(f, ast.FunctionDef): return copy.deepcopy(f)
    else: raise TypeError("Cannot handle functions provided as {:s}".format(type(f).__name__))
    # get the function definition
    fdef = t.body[0]
    assert isinstance(fdef, ast.FunctionDef)
    return fdef

def get_class_def(c: Union[Type[Any], str, ast.ClassDef]) -> ast.ClassDef:
    """Gets the ast.ClassDef for a class that is given as a class or as a string."""
    # parse the function
    if isinstance(c, str): t = ast.parse(remove_indentation(c))
    elif isinstance(c, ast.ClassDef): return copy.deepcopy(c)
    elif inspect.isclass(c): t = ast.parse(remove_indentation(inspect.getsource(c)))
    else: raise TypeError("Cannot handle classes provided as {:s}".format(type(c).__name__))
    # get the class definition
    cdef = t.body[0]
    assert isinstance(cdef, ast.ClassDef)
    return cdef

def get_method_by_name(c: ast.ClassDef, method_name: str) -> Optional[ast.FunctionDef]:
    for x in c.body:
        if isinstance(x, ast.FunctionDef) and x.name == method_name: return x
    return None

def _simplifyname(s: str) -> str:
    s = s.replace('gamehop.primitives.', '')
    w = s.split('.')
    if len(w) == 2:
        module = w[0]
        name = w[1]
        name = name.replace('Scheme', '')
        if module.lower() == name.lower(): return name
        else: return f"{module}.{name}"
    else: return s

def fqn(o) -> str:
    if inspect.isclass(o):
        if o.__module__ == '__main__': return "" + o.__name__.replace('Scheme', '')
        else: return _simplifyname(f"{o.__module__}.{o.__name__}")
    elif isinstance(o, _GenericAlias):
        return _simplifyname(str(o))
    else: return type(o).__name__

def typefqn(o) -> str:
    if isinstance(o, _GenericAlias):
        # remove generic arguments
        s = str(o)
        i = s.index('[')
        s = s[:i]
        # simplify name
        return _simplifyname(s)
    else:
        return fqn(inspect.getmro(o)[1])
