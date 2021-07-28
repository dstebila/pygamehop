import ast
from . import utils

class ASTFilterer(utils.NewNodeVisitor):
    # We might want to implement these later
    def visit_AnnAssign(self, node):
        raise NotImplementedError("Can't handle type annotated assignments")
    def visit_While(self, node):
        raise NotImplementedError(f"Can't handle, line {node.lineno} column {node.col_offset}")

        # even if we implement we won't want orelse bodies
        if len(node.orelse) != 0:
            raise NotImplementedError(f"Can't handle else in while loops, line {node.lineno} column {node.col_offset}")
        generic_visit(node)



    # AST node types we will not support
    def visit_Interactive(self, node):
        raise NotImplementedError(f"Can't handle interactive statements, line {node.lineno} column {node.col_offset}")
    def visit_FunctionType(self, node):
        raise NotImplementedError(f"Can't handle FunctypeType nodes, line {node.lineno} column {node.col_offset}")
    def visit_AsyncFunctionDef(self, node):
        raise NotImplementedError(f"Can't handle async function definitions, line {node.lineno} column {node.col_offset}")
    def visit_ClassDef(self, node):
        raise NotImplementedError(f"Can't handle class definitions, line {node.lineno} column {node.col_offset}")
    def visit_Delete(self, node):
        raise NotImplementedError(f"Can't handle delete statements, line {node.lineno} column {node.col_offset}")
    def visit_For(self, node):
        raise NotImplementedError(f"Can't handle for statements, line {node.lineno} column {node.col_offset}")
    def visit_With(self, node):
        raise NotImplementedError(f"Can't handle with statements, line {node.lineno} column {node.col_offset}")
    def visit_AsyncWith(self, node):
        raise NotImplementedError(f"Can't handle async with statements, line {node.lineno} column {node.col_offset}")
    def visit_Raise(self, node):
        raise NotImplementedError(f"Can't handle raise statements, line {node.lineno} column {node.col_offset}")
    def visit_Try(self, node):
        raise NotImplementedError(f"Can't handle try statements, line {node.lineno} column {node.col_offset}")
    def visit_Assert(self, node):
        raise NotImplementedError(f"Can't handle assert statements, line {node.lineno} column {node.col_offset}")
    def visit_Import(self, node):
        raise NotImplementedError(f"Can't handle import statements, line {node.lineno} column {node.col_offset}")
    def visit_ImportFrom(self, node):
        raise NotImplementedError(f"Can't handle import from statements, line {node.lineno} column {node.col_offset}")
    def visit_Global(self, node):
        raise NotImplementedError(f"Can't handle global statements, line {node.lineno} column {node.col_offset}")
    def visit_Nonlocal(self, node):
        raise NotImplementedError(f"Can't handle nonlocal statements, line {node.lineno} column {node.col_offset}")
    def visit_Pass(self, node):
        raise NotImplementedError(f"Can't handle pass statements, line {node.lineno} column {node.col_offset}")
    def visit_Break(self, node):
        raise NotImplementedError(f"Can't handle break statements, line {node.lineno} column {node.col_offset}")
    def visit_Continue(self, node):
        raise NotImplementedError(f"Can't handle continue statements, line {node.lineno} column {node.col_offset}")
    def visit_NamedExpr(self, node):
        raise NotImplementedError(f"Can't handle named expressions, line {node.lineno} column {node.col_offset}")
    def visit_Dict(self, node):
        raise NotImplementedError(f"Can't handle dictionaries, line {node.lineno} column {node.col_offset}")
    def visit_Set(self, node):
        raise NotImplementedError(f"Can't handle sets, line {node.lineno} column {node.col_offset}")
    def visit_List(self, node):
        raise NotImplementedError(f"Can't handle lists, line {node.lineno} column {node.col_offset}")
    def visit_ListComp(self, node):
        raise NotImplementedError(f"Can't handle list comprehensions, line {node.lineno} column {node.col_offset}")
    def visit_SetComp(self, node):
        raise NotImplementedError(f"Can't handle set comprehensions, line {node.lineno} column {node.col_offset}")
    def visit_DictComp(self, node):
        raise NotImplementedError(f"Can't handle dictionary comprehensions, line {node.lineno} column {node.col_offset}")
    def visit_GeneratorExp(self, node):
        raise NotImplementedError(f"Can't handle generator expressions, line {node.lineno} column {node.col_offset}")
    def visit_Await(self, node):
        raise NotImplementedError(f"Can't handle await expressions, line {node.lineno} column {node.col_offset}")
    def visit_Yield(self, node):
        raise NotImplementedError(f"Can't handle yield expressions, line {node.lineno} column {node.col_offset}")
    def visit_YieldFrom(self, node):
        raise NotImplementedError(f"Can't handle yield expressions, line {node.lineno} column {node.col_offset}")
    def visit_FormattedValue(self, node):
        raise NotImplementedError(f"Can't handle formatted value expressions, line {node.lineno} column {node.col_offset}")
    def visit_JoinedStr(self, node):
        raise NotImplementedError(f"Can't handle joined string expressions, line {node.lineno} column {node.col_offset}")
    def visit_Starred(self, node):
        raise NotImplementedError(f"Can't handle starred arguments, line {node.lineno} column {node.col_offset}")
    def visit_Slice(self, node):
        raise NotImplementedError(f"Can't handle slices, line {node.lineno} column {node.col_offset}")
    def visit_Expr(self, node): # this node is only used to wrap expressions that are used as statements
        raise NotImplementedError(f"Can't handle expressions as statements, line {node.lineno} column {node.col_offset}")

    # For these nodes we need to check that we can handle all their attributes

    def visit_FunctionDef(self, node):
        if len(node.decorator_list) != 0:
            raise NotImplementedError(f"Can't handle decorators, line {node.lineno} column {node.col_offset}")
        self.generic_visit(node)

    def visit_arguments(self, node):
        if len(node.kwonlyargs) != 0:
            raise NotImplementedError(f"Can't handle keyword only arguments, line {node.kwonlyargs[0].lineno} column {node.kwonlyargs[0].col_offset}")
        if len(node.posonlyargs) != 0:
            raise NotImplementedError(f"Can't handle position only arguments, line {node.posonlyargs[0].lineno} column {node.posonlyargs[0].col_offset}")
        if len(node.defaults) != 0:
            raise NotImplementedError(f"Can't handle defaults for arguments, line {node.defaults[0].lineno} column {node.defaults[0].col_offset}")
        if len(node.kw_defaults) != 0: # probably not needed since kwonlyargs are already forbidden
            raise NotImplementedError(f"Can't handle defaults for arguments, line {node.kw_defaults[0].lineno} column {node.kw_defaults[0].col_offset}")
        if node.vararg != None:
            raise NotImplementedError(f"Can't handle *args arguments, line {node.vararg.lineno} column {node.vararg.col_offset}")
        if node.kwarg != None:
            raise NotImplementedError(f"Can't handle **kwargs arguments, line {node.kwarg.lineno} column {node.kwarg.col_offset}")
        self.generic_visit(node)

    def visit_Call(self, node):
        if len(node.keywords) != 0:
            raise NotImplementedError(f"Can't handle function keyword arguments, line {node.lineno} column {node.col_offset}")

        self.generic_visit(node)

def filter_AST(node):
    filterer = ASTFilterer()
    filterer.visit(node)
