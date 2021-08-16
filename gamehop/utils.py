import ast
import difflib
import inspect
import types
from typing import Callable, Optional, Set, Union, List

def stringDiff(a,b):
    differences = difflib.ndiff(a.splitlines(keepends=True), b.splitlines(keepends=True))
    diffl = []
    for difference in differences:
        diffl.append(difference)
    print(''.join(diffl), end="\n")

class NewNodeVisitor(ast.NodeVisitor):
    """Adds the ability to handle List[ast.stmt] to ast.NodeVistor"""
    def visit(self, node):
        if isinstance(node, list):
            newnode = ast.Module()
            newnode.body = node
            super().visit(newnode)
        else:
            super().visit(node)

class NewNodeTransformer(ast.NodeTransformer):
    """Adds the ability to handle List[ast.stmt] to ast.NodeTransformer"""
    def visit(self, node):
        if isinstance(node, list):
            newnode = ast.Module()
            newnode.body = node
            return super().visit(newnode).body
        else:
            return super().visit(node)
    def generic_visit(self, node):
        if isinstance(node, list):
            newnode = ast.Module()
            newnode.body = node
            return super().generic_visit(newnode).body
        else:
            return super().generic_visit(node)

class VariableFinder(NewNodeVisitor):
    def __init__(self):
        self.stored_vars = list()
        self.loaded_vars = list()

    def visit_Name(self, node:ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            if node.id not in self.loaded_vars: self.loaded_vars.append(node.id)
        if isinstance(node.ctx, ast.Store):
            if node.id not in self.stored_vars: self.stored_vars.append(node.id)

class NameRenamer(NewNodeTransformer):
    """Replaces ids in Name nodes based on the provided mapping.  Raises a ValueError if the new name is already used in the function."""
    def __init__(self, mapping: dict, error_if_exists: bool):
        self.mapping = mapping
        self.error_if_exists = error_if_exists
    def visit_Name(self, node: ast.Name) -> ast.Name:
        if self.error_if_exists and (node.id in self.mapping.values()): raise ValueError("New name '{:s}' already exists in function".format(node.id))
        if node.id in self.mapping: return ast.Name(id=self.mapping[node.id], ctx=node.ctx)
        else: return node

class NamePrefixer(NewNodeTransformer):
    def __init__(self, prefix: str):
        self.prefix = prefix
        self.stored_vars: List[str] = list()
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

def stored_vars(node):
    varfinder = VariableFinder()
    varfinder.visit(node)
    return varfinder.stored_vars

def prefix_names(node, prefix):
    return NamePrefixer(prefix).visit(node)

def vars_depends_on(node: Optional[ast.AST]) -> List[str]:
    if isinstance(node, ast.Assign): return vars_depends_on(node.value)
    elif isinstance(node, ast.Attribute): return vars_depends_on(node.value)
    elif isinstance(node, ast.BinOp): return vars_depends_on(node.left) + vars_depends_on(node.right)
    elif isinstance(node, ast.Call): return vars_depends_on(node.func) + sum([vars_depends_on(arg) for arg in node.args], start=[])
    elif isinstance(node, ast.Compare): return vars_depends_on(node.left) + sum([vars_depends_on(c) for c in node.comparators], start=[])
    elif isinstance(node, ast.Constant): return []
    elif isinstance(node, ast.IfExp): return vars_depends_on(node.body) + vars_depends_on(node.test) + vars_depends_on(node.orelse)
    elif isinstance(node, ast.Name): return [node.id] if isinstance(node.ctx, ast.Load) else []
    elif isinstance(node, ast.Return): return [] if node.value == None else vars_depends_on(node.value)
    elif isinstance(node, ast.Tuple): return sum([vars_depends_on(e) for e in node.elts], start=[])
    else: raise NotImplementedError("Cannot handle AST objects of type {:s}".format(type(node).__name__))

def vars_assigns_to(node: ast.AST) -> List[str]:
    if isinstance(node, ast.Assign): return sum([vars_assigns_to(v) for v in node.targets], start=[])
    elif isinstance(node, ast.Attribute): return vars_assigns_to(node.value)
    elif isinstance(node, ast.BinOp): return []
    elif isinstance(node, ast.Call): return []
    elif isinstance(node, ast.Compare): return []
    elif isinstance(node, ast.Constant): return []
    elif isinstance(node, ast.IfExp): return []
    elif isinstance(node, ast.Name): return [node.id] if isinstance(node.ctx, ast.Store) else []
    elif isinstance(node, ast.Return): return []
    elif isinstance(node, ast.Tuple): return sum([vars_assigns_to(e) for e in node.elts], start=[])
    else: raise NotImplementedError("Cannot handle AST objects of type {:s}".format(type(node).__name__))

def get_function_def(f: Union[Callable, str, ast.FunctionDef]) -> ast.FunctionDef:
    """Gets the ast.FunctionDef for a function that is given as a function or as a string."""
    # parse the function
    if isinstance(f, types.FunctionType): 
        src = inspect.getsource(f)
        indentation = 0
        while src[indentation] == ' ': indentation += 1
        if indentation > 0:
            newsrc = []
            for line in src.splitlines():
                newsrc.append(line[indentation:])
            src = "\n".join(newsrc)
        t = ast.parse(src)
    elif isinstance(f, str): t = ast.parse(f)
    elif isinstance(f, ast.FunctionDef): return f
    else: raise TypeError("Cannot handle functions provided as {:s}".format(type(f).__name__))
    # get the function definition
    fdef = t.body[0]
    assert isinstance(fdef, ast.FunctionDef)
    return fdef
