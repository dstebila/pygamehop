import ast
from typing import Set, Union, List


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
        self.stored_vars = set()
        self.loaded_vars = set()

    def visit_Name(self, node:ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            self.loaded_vars.add(node.id)
        if isinstance(node.ctx, ast.Store):
            self.stored_vars.add(node.id)

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
        self.stored_vars: Set[str] = set()
    def visit_Name(self, node: ast.Name) -> ast.Name:
        # rename new stored variables, and remember that we did so
        if isinstance(node.ctx, ast.Store):
            self.stored_vars.add(node.id)
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
