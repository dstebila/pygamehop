import ast
import copy
from .. import utils

from typing import Dict, List

from ...inlining import internal

class ExpandNonCompactExpressions(utils.NewNodeTransformer):
    def value_to_name(self, node):
        # create a new assign statement to capture the value
        newvar = self.unique_variable_name()
        newassign = ast.Assign(
            targets = [ ast.Name(id = newvar, ctx = ast.Store) ],
            value = node
        )
        self.add_prelude_statement(newassign)

        # return a new Name node that refers to the value
        return ast.Name(id = newvar, ctx = ast.Load)

    def generic_visit(self, node):
        newval = super().generic_visit(node) # fix up children first

        # Keep  statements and compact values intact
        if isinstance(newval, ast.Constant) or isinstance(newval, ast.Name) or not isinstance(newval, ast.expr):
            return newval

        # At this point node must be an expression so newval will be too

        # Valid places for non-compact values in an assign or an Expr statement
        if isinstance(self.parent(), ast.Assign) or isinstance(self.parent(), ast.Expr):
            return newval

        # Anything else, assign value to a variable and use that instead
        return self.value_to_name(newval)


def expand_non_compact_expressions(f: ast.FunctionDef) -> None:
    """Modify (in place) the given function definition so that all non-compact
    (not a constant, not a variable name) expressions appear as assignments or
    as a statement (in an Expr).  New assignments to intermediate values are
    created if necessary to make this so."""

    ExpandNonCompactExpressions(var_format = "φ{:d}").visit(f)
    ast.fix_missing_locations(f)
