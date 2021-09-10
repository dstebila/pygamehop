import ast
import collections
import copy
import difflib
import inspect
import types
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union, TypeVar

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
    """Adds new abilities to the ast.NodeTtransformer class:

    - the ability to handle List[ast.stmt] using visit_statements()
    - keeping track of variables defined, respecting scopes.  i.e.
        variables defined functionDefs and ClassDefs are removed from the
        scope when those nodes have been processed.  Also, variables defined
        in the body or orelse of if statements are only added to the scope if
        they are defined in _both_ branches.  Locally, each branch keeps track
        of all variables it defines
    - keeping track of the parent of nodes as they are processed, available through
        parent(), which returns None if there is no parent, eg. if this a top-level node
    - if you need a new variable name, unique_variable_name() will give you one.
        each call returns a new name.

    Thinks to keep in mind:
    - scopes for ifs are implemented with a visit_If method.  If you override
        this method then you are responsible for keeping track of the scopes
        (if scopes are being used)
    - if you define __init__ then you must call super().__init__() to get
        the local variables set up correctly
     """
    def __init__(self, counter=0):
        self.prelude_statements: List[ast.stmt] = list()
        self.unique_string_counter: int = counter

        # When we encounter these types of nodes we insert any
        # prelude statements before the node.
        self.prelude_anchor_types = { ast.Assign, ast.Return, ast.FunctionDef, ast.If, ast.Expr }
        self.new_scope_types = { ast.FunctionDef, ast.ClassDef }

        # Keep track of the variables that are in scope
        # We will push a new set when a new scope (eg function, class def ) is
        # created
        self.scopes: List[List[str]] = list()
        self.scopes.append(list())

        # Keep track of the parent of the node being transformed
        self.ancestors = list()

    def unique_variable_name(self, var_format = '_var_{:d}'):
        v = var_format.format(self.unique_string_counter)
        self.unique_string_counter += 1
        return v

    # Prelude statements

    def add_prelude_statement(self, statement: ast.stmt) -> None:
        self.prelude_statements.append(statement)

    def pop_prelude_statements(self) -> List[ast.stmt]:
        new_statements = self.prelude_statements[:]
        self.prelude_statements = list()
        return new_statements


    # scopes

    def new_scope(self) -> None:
        self.scopes.append(list())

    def pop_scope(self) -> None:
        self.scopes.pop()

    def in_scope(self, varname: str) -> bool:
        for s in self.scopes[::-1]:
            if varname in s: return True
        return False

    def add_var_to_scope(self, varname: str) -> None:
        if not varname in self.scopes[-1]:
            self.scopes[-1].append(varname)

    def add_var_to_scope_from_nodes(self, nodes: Union[ast.AST, List[ast.AST]]) -> None:
        if isinstance(nodes, ast.AST):
            nodes = [ nodes ]
        for s in nodes:
            if type(s) == ast.Assign:
                for v in vars_assigns_to(s):
                    self.add_var_to_scope(v)


    def vars_in_scope(self) -> List[str]:
        return sum(self.scopes, [])

    def vars_in_local_scope(self) -> List[str]:
        return list(self.scopes[-1])


    # Keep track of parent of each node
    def parent(self):
        if len(self.ancestors) < 1:
            return None
        return self.ancestors[-1]

    def push_parent(self, node):
        self.ancestors.append(node)

    def pop_parent(self):
        self.ancestors.pop()

    def visit_statements(self, stmts: List[ast.stmt]) -> List[ast.stmt]:
        # overwrite the old statements with whatever we get back
        stmts[:] = sum( [ ensure_list(self.visit(stmt)) for stmt in stmts ] , [])
        return stmts

    def visit_If(self, node):
        self.push_parent(node)
        # ifs need special attention because a variable may be assigned to
        # in one branch but not the other


        # test is in common
        node.test = self.visit(node.test)

        # create a new scope for the body so that we don't count them as
        # in scope in the orelse
        self.new_scope()
        node.body = sum( [ ensure_list(self.visit(child)) for child in node.body ] , [])
        ifscope = self.vars_in_local_scope()
        self.pop_scope()

        # create a new scope for the orelse so that we don't count them as
        # in scope later when the orelse may not have run
        self.new_scope()
        node.orelse = sum( [ ensure_list(self.visit(child)) for child in node.orelse ], [])
        elsescope = self.vars_in_local_scope()
        self.pop_scope()

        # we only want to keep variables that were assigned to
        # in _both_ branches, otherwise they may not be defined
        bothscopes = ifscope + elsescope
        for v in bothscopes:
            if bothscopes.count(v) == 2:
                self.add_var_to_scope(v)

        self.pop_parent()
        return self.pop_prelude_statements() + [ node ]


    def generic_visit(self, node):

        # we need to create any new scope before visiting children
        if type(node) in self.new_scope_types:
            self.new_scope()

        # We need to set this node as parent before we visit its childen
        self.push_parent(node)
        visit_val = super().generic_visit(node)  # this call will only visit children
        self.pop_parent()

        # Remove the scope now that it is complete
        if type(node) in self.new_scope_types:
            self.pop_scope()


        if not type(node) in self.prelude_anchor_types or len(self.prelude_statements) == 0:
            self.add_var_to_scope_from_nodes(visit_val)
            return visit_val

        # Ensure we have a list of new nodes to add
        visit_val = ensure_list(visit_val)

        ret_val = self.pop_prelude_statements() + visit_val
        self.add_var_to_scope_from_nodes(ret_val)

        return ret_val

class VariableFinder(NewNodeVisitor):
    def __init__(self):
        self.stored_vars = list()
        self.loaded_vars = list()
        super().__init__()

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
        super().__init__()

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

class NameNodeReplacer(NewNodeTransformer):
    """Replaces all instances of a Name node with a given node, for each name in the given dictionary of replacements."""
    def __init__(self, replacements: Dict[str, ast.expr]):
        self.replacements = replacements
        super().__init__()
    def visit_Name(self, node):
        if node.id in self.replacements: return self.replacements[node.id]
        else: return node

class AttributeNodeReplacer(NewNodeTransformer):
    """Replaces all instances of an Attribute node (possibly multiple attributes deep) with a Name node with the given name."""
    def __init__(self, needle: List[str], replacement: str):
        self.needle = needle
        self.replacement = replacement
        super().__init__()
    def visit_Attribute(self, node):
        # work backward from the end of the attribute and see if it matches the thing we're looking for
        curr_a = node
        for i, n in enumerate(reversed(self.needle)):
            if isinstance(curr_a, ast.Attribute):
                if curr_a.attr == n:
                    # so far so good... advance to the next part of the node
                    curr_a = curr_a.value
                    continue
                else: break
            elif isinstance(curr_a, ast.Name):
                if i == len(self.needle) - 1 and curr_a.id == n:
                    # we found an exact match! do the replacement
                    return ast.Name(id=self.replacement, ctx=node.ctx)
                else: break
        # we didn't find an exact match... but recurse on the inner part of this attribute in case it's a match
        return ast.Attribute(value=self.visit(node.value), attr=node.attr, ctx=node.ctx)

def stored_vars(node):
    varfinder = VariableFinder()
    varfinder.visit(node)
    return varfinder.stored_vars

def vars_depends_on(node: Optional[ast.AST]) -> List[str]:
    if isinstance(node, ast.Assign):
        r = []
        # we have to go through the targets to find any attributed objects that are assigned to, since this assignment statement depends on them
        for t in node.targets: r.extend(vars_depends_on(t))
        r.extend(vars_depends_on(node.value))
        return r
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
    elif isinstance(node, ast.arg): return [ node.arg ]
    else: raise NotImplementedError("Cannot handle AST objects of type {:s}".format(type(node).__name__))

def vars_assigns_to(node: Union[ast.AST, List[ast.stmt]]) -> List[str]:
    if isinstance(node, list): return sum([vars_assigns_to(stmt) for stmt in node], start=[])
    elif isinstance(node, ast.Assign): return sum([vars_assigns_to(v) for v in node.targets], start=[])
    elif isinstance(node, ast.Attribute):
        if isinstance(node.ctx, ast.Store): return vars_depends_on(node.value)
        else: return []
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

T = TypeVar('T')
def ensure_list(thing: Union[T, List[T]]) -> List[T]:
    if isinstance(thing, list):
        return thing
    else:
        return [ thing ]
