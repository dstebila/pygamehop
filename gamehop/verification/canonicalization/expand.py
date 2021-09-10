import ast
import copy
from .. import utils

from typing import Dict, List

from ...inlining import internal

class ExtractCallArguments(utils.NewNodeTransformer):
    """For every call node, if any of its arguments are not a constant or a variable
    name, extract that argument into a new assign statement to a temporary variable.
    The new assign statements are logged in the self.predecessors member.
    Temporary variables names will be assigned starting at counter, and the counter
    will be updated as new variables are added. The inner most arguments will be
    extracted first."""
    def value_to_name(self, node):
        # create a new assign statement to capture the value
        newvar = self.unique_variable_name("φ{:d}")
        newassign = ast.Assign(
            targets = [ ast.Name(id = newvar, ctx = ast.Store) ],
            value = node
        )
        self.add_prelude_statement(newassign)

        # return a new Name node that refers to the value
        return ast.Name(id = newvar, ctx = ast.Load)


    def visit_Call(self, node):
        self.generic_visit(node)  # fix up all children first

        # Valid places for a call are value for an assign value or an Expr (bare function call)
        if isinstance(self.parent(), ast.Assign) or isinstance(self.parent(), ast.Expr):
            return node

        return self.value_to_name(node)

def call_arguments(f: ast.FunctionDef) -> None:
    """Modify (in place) the given function definition so that all non-trivial
    (not a constant, not a variable name) arguments to function calls appear as
    intermediate assignments immediately preceding the function call."""

    ExtractCallArguments().visit(f)
    ast.fix_missing_locations(f)

class ExtractIfExpArguments(utils.NewNodeTransformer):
    """For every IfExp node, if any of its arguments are not a constant or a variable
    name, extract that argument into a new assign statement to a temporary variable.
    The new assign statements are logged in the self.predecessors member.
    Temporary variables names will be assigned starting at counter, and the counter
    will be updated as new variables are added. The inner most arguments will be
    extracted first."""

    def value_to_name(self, node):
        # create a new assign statement to capture the value
        newvar = self.unique_variable_name("φifexp{:d}")
        newassign = ast.Assign(
            targets = [ ast.Name(id = newvar, ctx = ast.Store) ],
            value = node
        )
        self.add_prelude_statement(newassign)

        # return a new Name node that refers to the value
        return ast.Name(id = newvar, ctx = ast.Load)

    def fix_non_compact_value(self, value):
        if isinstance(value, ast.Constant) or isinstance(value, ast.Name):
            return value
        return self.value_to_name(value)

    def visit_IfExp(self, node):
        self.generic_visit(node)
        node.body = self.fix_non_compact_value(node.body)
        node.test = self.fix_non_compact_value(node.test)
        node.orelse = self.fix_non_compact_value(node.orelse)
        return node

def ifexpressions(f: ast.FunctionDef) -> None:
    """Modify (in place) the given function definition so that all non-trivial
    (not a constant, not a variable name) arguments to if expressions (b if c else d)
    appear as intermediate assignments immediately preceding the if expression."""
    ExtractIfExpArguments().visit(f)
    ast.fix_missing_locations(f)
