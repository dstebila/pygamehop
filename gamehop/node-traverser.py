import ast
import types
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union, TypeVar


class NodeTraverser():
    def __new__(cls, *args, **kwargs) -> None:
        # set up all variables that we depend on
        # do it in __new__ so that subclasse don't need to call super().__init__()
        instance = super(NodeTraverser, cls).__new__(cls, *args, **kwargs)
        return instance

    def visit(self, node: ast.AST) -> ast.AST:
        # call visit_Blah for this type of node

        print(ast.dump(node))
        visit_function_name = f"visit_{type(node).__name__}"
        if hasattr(self, visit_function_name):
            visit_function = getattr(self, visit_function_name)
            return visit_function(node)
        else:
            return self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        print(ast.dump(node))

    def visit_stmts(self, stmts: List[ast.stmt]):
        return [ self.generic_visit(stmt) for stmt in stmts]

    def visit_exprs(self, exprs: List[ast.expr]):
        return [ self.generic_visit(expr) for expr in exprs ]
    def visit_child_list(self, l: List):
        return l

    def generic_visit(self, node: ast.AST) -> ast.AST:
        # iterate over all children
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
                    self.visit(child)
                else:
                    if child != None:
                        print(child)
        return node

# testing stuff, remove later
import inspect
def f():
    pass

f_ast = ast.parse(inspect.getsource(f))
nt = NodeTraverser()
nt.visit(f_ast)
print(ast.dump(f_ast))
