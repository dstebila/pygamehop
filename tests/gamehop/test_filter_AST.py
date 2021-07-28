import ast
import inspect
import unittest

import gamehop.filterast
import gamehop.inlining.internal as internal



# Interactive node example?

def f_Expr():
    myfunc(1)

# FunctionType node example?

def f_AsyncFunctionDef():
    async def myfunc(): pass
def f_ClassDef():
    class someclass:
        def somefunc(self): pass
def f_Delete():
    a = 3
    del(a)

# AnnAssign to tested

def f_For():
    for a in S: pass

# this one is a string because otherwise we would need to put it in an async function, which is another case.
async_for_str = "async for i in S: pass"

def f_With():
    b = 1
    with a as b:
        pass
async_with_str = "async with a as b: pass"

def f_Raise():
    raise ValueError("blah")
def f_Try():
    try:
        pass
    except:
        pass
def f_Assert():
    assert(True)
def f_Import():
    import blarg
def f_ImportFrom():
    from . import blarg
def f_Global():
    global x
def f_Nonlocal():
    x = 1
    def myfunc():
        nonlocal x

# these are in strings because they usually only come in for or while loops, which are other cases
pass_str = "pass"
break_str = "break"
continue_str = "continue"

def f_NamedExpr():
    (x := 1)
def f_Dict():
    x = {}
def f_Set():
    x = { 1 }
def f_List():
    x = []
def f_ListComp():
    x = [ i for i in S ]
def f_SetComp():
    x = { i for i in S }
def f_DictComp():
    x = { i:i for i in S }
def f_GeneratorExp():
    x = ( i for i in S )

await_str = "await myfunc()"

def f_Yield():
    yield 1
def f_YieldFrom():
    yield from myfunc()
def f_FormattedValue():
    x = f"{var}"
def f_JoinedStr():
    x = f"blah"

starred_str = "*b = it"

def f_Slice():
    x = mylist[1:2]

# These tests are for nodes that are supported, but certain attributes are forbidden

def f_decorators():
    @mydecorator
    def myfunc(): pass
def f_posonlyargs():
    def myfunc(a, /, b): pass
def f_kwonlyargs():
    def myfunc(a, *, b): pass
def f_starargs():
    def myfunc(*args): pass
def f_kwstarargs():
    def myfunc(**kwargs): pass
def f_defaultargs():
    def myfunc(a=1): pass
def f_kwargscall():
    x = myfunc(a = 1)

# type_ignore?

# The following have no tests because they only appear in other nodes that are already forbidden, so we can't create isolated cases for them:
#   comprehension, excepthandler, keyword, alias, withitem,
# Similar for these attributes:
#   kw_defaults


class TestFilterAST(unittest.TestCase):
    def test_Expr(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(internal.get_function_def(f_Expr))
    def test_AsyncFunctionDef(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(internal.get_function_def(f_AsyncFunctionDef))
    def test_ClassDef(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(internal.get_function_def(f_ClassDef))
    def test_Delete(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(internal.get_function_def(f_Delete))
    def test_For(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(internal.get_function_def(f_For))
    def test_AsyncFor(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(ast.parse(async_for_str))
    def test_With(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(internal.get_function_def(f_With))
    def test_AsyncWith(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(ast.parse(async_with_str))
    def test_Raise(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(internal.get_function_def(f_Raise))
    def test_Try(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(internal.get_function_def(f_Try))
    def test_Assert(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(internal.get_function_def(f_Assert))
    def test_Import(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(internal.get_function_def(f_Import))
    def test_ImportFrom(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(internal.get_function_def(f_ImportFrom))
    def test_Global(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(internal.get_function_def(f_Global))
    def test_Nonlocal(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(internal.get_function_def(f_Nonlocal))
    def test_Pass(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(ast.parse(pass_str))
    def test_Break(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(ast.parse(break_str))
    def test_Continue(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(ast.parse(continue_str))
    def test_NamedExpr(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(internal.get_function_def(f_NamedExpr))
    def test_Dict(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(internal.get_function_def(f_Dict))
    def test_Set(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(internal.get_function_def(f_Set))
    def test_List(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(internal.get_function_def(f_List))
    def test_ListComp(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(internal.get_function_def(f_ListComp))
    def test_SetComp(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(internal.get_function_def(f_SetComp))
    def test_DictComp(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(internal.get_function_def(f_DictComp))
    def test_GeneratorExp(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(internal.get_function_def(f_GeneratorExp))
    def test_Await(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(ast.parse(await_str))
    def test_Yield(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(internal.get_function_def(f_Yield))
    def test_YieldFrom(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(internal.get_function_def(f_YieldFrom))
    def test_YieldFormattedValue(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(internal.get_function_def(f_FormattedValue))
    def test_JoinedStr(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(internal.get_function_def(f_JoinedStr))
    def test_Starred(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(ast.parse(starred_str))
    def test_Slice(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(internal.get_function_def(f_Slice))
    def test_Decorator(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(internal.get_function_def(f_decorators))
    def test_Posonlyargs(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(internal.get_function_def(f_posonlyargs))
    def test_Kwonlyargs(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(internal.get_function_def(f_kwonlyargs))
    def test_Starargs(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(internal.get_function_def(f_starargs))
    def test_Kwstarargs(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(internal.get_function_def(f_kwstarargs))
    def test_defaultargs(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(internal.get_function_def(f_defaultargs))
    def test_kwargscall(self):
        with self.assertRaises(NotImplementedError):
            gamehop.filterast.filter_AST(internal.get_function_def(f_kwargscall))
