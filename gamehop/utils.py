import ast
import collections
import copy
import difflib
import inspect
import types
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union

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
    prelude_statements: List[ast.stmt] = list()
    unique_string_counter: int = 0

    def unique_variable_name(self):
        v = f'_var_{self.unique_string_counter}'
        self.unique_string_counter += 1
        return v

    def add_prelude_statement(self, statement: ast.stmt) -> None:
        self.prelude_statements.append(statement)

    def pop_prelude_statements(self) -> List[ast.stmt]:
        new_statements = self.prelude_statements[:]
        self.prelude_statements = list()
        return new_statements

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

def rename_variables(f: Union[Callable, str, ast.FunctionDef], mapping: dict, error_if_exists = True) -> ast.FunctionDef:
    """Returns a copy of the function with all the variables in the given function definition renamed based on the provided mapping.  Raises a ValueError if the new name is already used in the function."""
    retvalue = NameRenamer(mapping, error_if_exists).visit(get_function_def(f))
    # rename any relevant variables in the function arguments
    for arg in retvalue.args.args:
        if error_if_exists and (arg.arg in mapping.values()): raise ValueError("New name '{:s}' already exists in function".format(arg.arg))
        if arg.arg in mapping: arg.arg = mapping[arg.arg]
    return retvalue

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

def prefix_names(node, prefix):
    return NamePrefixer(prefix).visit(node)

class NameNodeReplacer(NewNodeTransformer):
    """Replaces all instances of a Name node with a given node, for each name in the given dictionary of replacements."""
    def __init__(self, replacements: Dict[str, ast.expr]):
        self.replacements = replacements
    def visit_Name(self, node):
        if node.id in self.replacements: return self.replacements[node.id]
        else: return node

def stored_vars(node):
    varfinder = VariableFinder()
    varfinder.visit(node)
    return varfinder.stored_vars

def vars_depends_on(node: Optional[ast.AST]) -> List[str]:
    if isinstance(node, ast.Assign): return vars_depends_on(node.value)
    elif isinstance(node, ast.Attribute): return vars_depends_on(node.value)
    elif isinstance(node, ast.BinOp): return vars_depends_on(node.left) + vars_depends_on(node.right)
    elif isinstance(node, ast.Call): return vars_depends_on(node.func) + sum([vars_depends_on(arg) for arg in node.args], start=[])
    elif isinstance(node, ast.Compare): return vars_depends_on(node.left) + sum([vars_depends_on(c) for c in node.comparators], start=[])
    elif isinstance(node, ast.Constant): return []
    elif isinstance(node, ast.Expr): return vars_depends_on(node.value)
    elif isinstance(node, ast.IfExp): return vars_depends_on(node.body) + vars_depends_on(node.test) + vars_depends_on(node.orelse)
    elif isinstance(node, ast.Name): return [node.id] if isinstance(node.ctx, ast.Load) else []
    elif isinstance(node, ast.Return): return [] if node.value == None else vars_depends_on(node.value)
    elif isinstance(node, ast.Tuple): return sum([vars_depends_on(e) for e in node.elts], start=[])
    else: raise NotImplementedError("Cannot handle AST objects of type {:s}".format(type(node).__name__))

def vars_assigns_to(node: Union[ast.AST, List[ast.stmt]]) -> List[str]:
    if isinstance(node, list): return sum([vars_assigns_to(stmt) for stmt in node], start=[])
    elif isinstance(node, ast.Assign): return sum([vars_assigns_to(v) for v in node.targets], start=[])
    elif isinstance(node, ast.Attribute): return vars_assigns_to(node.value)
    elif isinstance(node, ast.BinOp): return []
    elif isinstance(node, ast.Call): return []
    elif isinstance(node, ast.Compare): return []
    elif isinstance(node, ast.Constant): return []
    elif isinstance(node, ast.Expr): return []
    elif isinstance(node, ast.IfExp): return []
    elif isinstance(node, ast.Name): return [node.id] if isinstance(node.ctx, ast.Store) else []
    elif isinstance(node, ast.Return): return []
    elif isinstance(node, ast.Tuple): return sum([vars_assigns_to(e) for e in node.elts], start=[])
    else: raise NotImplementedError("Cannot handle AST objects of type {:s} ({:s})".format(type(node).__name__, ast.unparse(node)))

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
