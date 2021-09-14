import ast
import types
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union, TypeVar


class NodeTraverser():
    def __new__(cls):
        # set up all variables that we depend on
        # do it in __new__ so that subclasse don't need to call super().__init__()
        instance = super(NodeTraverser, cls).__new__(cls)
        return instance

    def visit(self, node: ast.AST) -> ast.AST:
        # call visit_Blah for this type of node
        print(type(node).__name__)
        visit_function_name = f"visit_{type(node).__name__}"
        if hasattr(self, visit_function_name):
            visit_function = getattr(self, visit_function_name)
            return visit_function(node)
        else:
            return self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        return self.generic_visit(node)

    def visit_stmts(self, stmts: List[ast.stmt]) -> List[ast.AST]:
        return [ self.visit(stmt) for stmt in stmts]

    def visit_exprs(self, exprs: List[ast.expr]) -> List[ast.AST]:
        return [ self.visit(expr) for expr in exprs ]

    def visit_child_list(self, l: List) -> List:
        return l

    def generic_visit(self, node: ast.AST) -> ast.AST:
        ''' Iterate over all childern of the given node, listed in node._fields.
            This means:
            - if a child is a AST node, then visit() it and replace the current node
                 with the return value
            - if a child is a list of ast.stmt, then visit_stmts() the list and replace the
                 current list with the return value
            - if a child is a list of ast.expr, then visit_exprs() the list and replace the
                 current list with the return value
            - if a child is a list of anything else, then visit_child_list() the list and replace the
                 current list with the return value
            - all other children are not visited
            - empty lists are not visited
        '''
        for field_name in node._fields:
            if hasattr(node, field_name):
                child = getattr(node, field_name)

                if type(child) == list:
                    if len(child) == 0: continue
                    if isinstance(child[0], ast.stmt):
                        child[:] = self.visit_stmts(child)
                    elif isinstance(child[0], ast.expr):
                        child[:] = self.visit_exprs(child)
                    else:
                        child[:] = self.visit_child_list(child)

                elif isinstance(child, ast.AST):
                    setattr(node, field_name, self.visit(child))

                else:
                    # for now, do nothing, but maybe in the future we will want
                    # to visit non-node fields
                    pass
        return node
