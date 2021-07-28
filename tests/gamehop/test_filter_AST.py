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
    for a in range(1,2): pass

# this one is a string because otherwise we would need to put it in an async function, which is another case.
async_for_str = "async for i in range(1,2): pass"

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
