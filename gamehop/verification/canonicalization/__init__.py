import ast
import copy
import secrets
from typing import Dict, List, Union

from ...inlining import internal
from ... import utils
from ... import node_traverser as nt
from ... import node_graph as ng
from ... import bits 

def canonicalize_function_name(f: ast.FunctionDef, name = 'f') -> None:
    """Modify (in place) the given function definition to have a canonical name."""
    f.name = name
    ast.fix_missing_locations(f)

def canonicalize_variable_names(f: ast.FunctionDef, prefix = 'v') -> None:
    """Modify (in place) the given function definition to give variables canonical names."""
    # first rename everything to a random string followed by a counter
    # then rename them to v0, v1, v2, ...
    tmpname = 'tmp_' + secrets.token_hex(10)
    # set up the mappings
    vars = internal.find_all_variables(f)
    mappings_1stpass = dict()
    mappings_2ndpass = dict()
    for i in range(len(vars)):
        mappings_1stpass[vars[i]] = '{:s}{:d}'.format(tmpname, i)
        mappings_2ndpass[mappings_1stpass[vars[i]]] = '{:s}{:d}'.format(prefix, i)
    utils.rename_function_body_variables(f, mappings_1stpass)
    utils.rename_function_body_variables(f, mappings_2ndpass)
    ast.fix_missing_locations(f)

# apparently not used
def contains_name(node: Union[ast.AST, List], name: str) -> bool:
    """Determines whether the given node (or list of nodes) contains a variable with the given name."""
    return any( True for n in nt.nodes(node, nodetype = ast.Name) if n.id == name )

class VariableCollapser(nt.NodeTraverser):
    def visit_Name(self, node):
        node = self.generic_visit(node)
        if not isinstance(node.ctx, ast.Load):
            return node

        if not self.in_scope(node.id):   # this includes cases like function names
            return node

        value = self.var_value(node.id)

        if isinstance(value, ast.Constant) or isinstance(value, ast.Name) or isinstance(value, ast.Tuple) or isinstance(value, ast.Attribute):
            return copy.deepcopy(value)

        return node

    def visit_Attribute(self, node):
        node = self.generic_visit(node)
        if not isinstance(node.ctx, ast.Load):
            return node

        fqn = ".".join(bits.attribute_fqn(node))

        if not self.in_scope(fqn):   # this includes cases like function names
            return node

        value = self.var_value(fqn)

        if isinstance(value, ast.Constant) or isinstance(value, ast.Name) or isinstance(value, ast.Tuple) or isinstance(value, ast.Attribute):
            return copy.deepcopy(value)

        return node


def collapse_useless_assigns(f: ast.FunctionDef) -> None:
    """Modify (in place) the given function definition to remove all lines containing tautological/useless assignments. For example, if the code contains a line "x = a" followed by a line "y = x + b", it replaces all subsequent instances of x with a, yielding the single line "y = a + b", up until x is set in another assignment statement.  Handles tuples.  Doesn't handle any kind of logic involving if statements or loops."""

    VariableCollapser().visit(f)
    ast.fix_missing_locations(f)

# apparently not used
def assignee_vars(stmt: ast.Assign) -> List[str]:
    if len(stmt.targets) != 1: raise NotImplementedError("Cannot handle assignment statements with multiple targets")
    if isinstance(stmt.targets[0], ast.Name): return [stmt.targets[0].id]
    elif isinstance(stmt.targets[0], ast.Tuple):
        ret = list()
        for x in stmt.targets[0].elts:
            if not isinstance(x, ast.Name): raise NotImplementedError("Cannot handle tuples containing things other than variables")
            ret.append(x.id)
        return ret
    else: raise NotImplementedError("Cannot handle assignments with left sides of the type " + str(type(stmt.targets[0]).__name__))

def canonicalize_line_order(f: ast.FunctionDef, extra_dependencies: Dict[str, List[str]] = {}) -> None:
    """Modify (in place) the given function definition to canonicalize the order of lines
    based on the order in which the returned variable depends on previous lines. Lines
    that do not affect the return variable are removed.  Assumes that the return statement
    is the last statement in the function body"""
    G = ng.Graph.from_stmts(f.body, extra_dependencies)
    assert isinstance(f.body[-1], ast.Return)
    return_stmt = f.body[-1]
    G = G.reachable_subgraph([ return_stmt ], True)
    G.canonical_sort()
    f.body = G.vertices

class ArgumentReorderer(nt.NodeTraverser):
    def visit_FunctionDef(self, node):
        # visit the body to get the scope set up
        node = self.generic_visit(node)
        s = self.local_scope()
        node.args.args = [ ast.arg(arg = parname , annotation = parannotation) for parname, parannotation in s.parameters_loaded() ]
        return node

def canonicalize_argument_order(f: ast.FunctionDef) -> None:
    """Modify (in place) the given function definition to canonicalize the order of the arguments
    based on the order in which the variables appear.  Arguments that are not referred to are removed.
    Note that this also applies to any inner functions."""

    ArgumentReorderer().visit(f)
    ast.fix_missing_locations(f)

class LambdaReplacer(nt.NodeTraverser):
    def visit_Call(self, node):
        node = self.generic_visit(node)
        if not isinstance(node.func, ast.Name): return node
        if not self.in_scope(node.func.id): return node
        lam = self.var_value(node.func.id)
        if not isinstance(lam, ast.Lambda): return node

        lamargs = lam.args.args
        callargs = node.args
        assert len(lamargs) == len(callargs)
        lambody = copy.deepcopy(lam.body)
        mappings = dict()
        for i in range(len(lamargs)):
            mappings[lamargs[i].arg] = callargs[i]
        return utils.NameNodeReplacer(mappings).visit(lambody)


def inline_lambdas(f: ast.FunctionDef) -> None:
    """Modify (in place) the given function definition to replace all calls to lambdas with their body."""
    f = LambdaReplacer().visit(f)
    ast.fix_missing_locations(f)
