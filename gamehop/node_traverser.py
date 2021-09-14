import ast
import types
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union, TypeVar

T = TypeVar('T')
def ensure_list(thing: Union[T, List[T]]) -> List[T]:
    if isinstance(thing, list):
        return thing
    else:
        return [ thing ]

def glue_list_and_vals(vals: List[Union[T, List[T], None]]) -> List[T]:
    ret_val: List[T] = list()
    for v in vals:
        if isinstance(v, list):
            ret_val.extend(v)
        else:
            if v is None:
                continue
            else:
                ret_val.append(v)
    return ret_val

class NodeTraverser():
    def __new__(cls, *args, **kwargs):
        # set up all variables that we depend on
        # do it in __new__ so that subclasse don't need to call super().__init__()
        instance = super(NodeTraverser, cls).__new__(cls)
        return instance

    def visit(self, node: ast.AST):
        # call visit_Blah for this type of node
        visit_function_name = f"visit_{type(node).__name__}"
        if hasattr(self, visit_function_name):
            visit_function = getattr(self, visit_function_name)
            return visit_function(node)
        else:
            return self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Optional[ast.AST]:
        return self.generic_visit(node)

    def visit_stmts(self, stmts: List[ast.stmt]) -> List[ast.AST]:
        return glue_list_and_vals([ self.visit(stmt) for stmt in stmts])

    def visit_exprs(self, exprs: List[ast.expr]) -> List[ast.AST]:
        return glue_list_and_vals([ self.visit(expr) for expr in exprs ])

    def visit_child_list(self, children: List) -> List:
        return glue_list_and_vals([ self.visit(v) for v in children ])

    def generic_visit(self, node: ast.AST) -> Optional[ast.AST]:
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
        if node is None: return None
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
                    new_child = self.visit(child)
                    if new_child is None:
                        delattr(node, field_name)
                    else:
                        setattr(node, field_name, new_child)
                else:
                    # for now, do nothing, but maybe in the future we will want
                    # to visit non-node fields
                    pass
        return node
