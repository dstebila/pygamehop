import ast
import inspect
import unittest

import gamehop.filterast
import gamehop.inlining.internal as internal


# AnnAssign to tested

# type_ignore?

# The following have no tests because they only appear in other nodes that are already forbidden, so we can't create isolated cases for them:
#   comprehension, excepthandler, keyword, alias, withitem,
# Similar for these attributes:
#   kw_defaults

class TestFilterAST(unittest.TestCase):

    # Interactive node example?
    def test_Expr(self):
        def f_Expr(): myfunc(1)
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(internal.get_function_def(f_Expr))

    # FunctionType node examples
    def test_AsyncFunctionDef(self):
        def f_AsyncFunctionDef():
            async def myfunc(): pass
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(internal.get_function_def(f_AsyncFunctionDef))

    def test_ClassDef(self):
        def f_ClassDef():
            class someclass:
                def somefunc(self): pass
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(internal.get_function_def(f_ClassDef))

    def test_Delete(self):
        def f_Delete():
            a = 3
            del(a)
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(internal.get_function_def(f_Delete))

    def test_For(self):
        def f_For():
            for a in S: pass
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(internal.get_function_def(f_For))

    def test_AsyncFor(self):
        # this one is a string because otherwise we would need to put it in an async function, which is another case.
        async_for_str = "async for i in S: pass"
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(ast.parse(async_for_str))

    def test_With(self):
        def f_With():
            b = 1
            with a as b: pass
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(internal.get_function_def(f_With))

    def test_AsyncWith(self):
        async_with_str = "async with a as b: pass"
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(ast.parse(async_with_str))

    def test_Raise(self):
        def f_Raise(): raise ValueError("blah")
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(internal.get_function_def(f_Raise))

    def test_Try(self):
        def f_Try():
            try: pass
            except: pass
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(internal.get_function_def(f_Try))

    def test_Assert(self):
        def f_Assert(): assert(True)
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(internal.get_function_def(f_Assert))

    def test_Import(self):
        def f_Import(): import blarg
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(internal.get_function_def(f_Import))

    def test_ImportFrom(self):
        def f_ImportFrom(): from . import blarg
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(internal.get_function_def(f_ImportFrom))

    def test_Global(self):
        def f_Global(): global x
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(internal.get_function_def(f_Global))

    def test_Nonlocal(self):
        def f_Nonlocal():
            x = 1
            def myfunc(): nonlocal x
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(internal.get_function_def(f_Nonlocal))

    # these are in strings because they usually only come in for or while loops, which are other cases

    def test_Pass(self):
        pass_str = "pass"
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(ast.parse(pass_str))

    def test_Break(self):
        break_str = "break"
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(ast.parse(break_str))

    def test_Continue(self):
        continue_str = "continue"
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(ast.parse(continue_str))

    def test_NamedExpr(self):
        def f_NamedExpr(): (x := 1)
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(internal.get_function_def(f_NamedExpr))

    def test_Dict(self):
        def f_Dict(): x = {}
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(internal.get_function_def(f_Dict))

    def test_Set(self):
        def f_Set(): x = { 1 }
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(internal.get_function_def(f_Set))

    def test_List(self):
        def f_List(): x = []
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(internal.get_function_def(f_List))

    def test_ListComp(self):
        def f_ListComp(): x = [ i for i in S ]
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(internal.get_function_def(f_ListComp))

    def test_SetComp(self):
        def f_SetComp(): x = { i for i in S }
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(internal.get_function_def(f_SetComp))

    def test_DictComp(self):
        def f_DictComp(): x = { i:i for i in S }
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(internal.get_function_def(f_DictComp))

    def test_GeneratorExp(self):
        def f_GeneratorExp(): x = ( i for i in S )
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(internal.get_function_def(f_GeneratorExp))

    def test_Await(self):
        await_str = "await myfunc()"
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(ast.parse(await_str))

    def test_Yield(self):
        def f_Yield(): yield 1
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(internal.get_function_def(f_Yield))

    def test_YieldFrom(self):
        def f_YieldFrom(): yield from myfunc()
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(internal.get_function_def(f_YieldFrom))

    def test_FormattedValue(self):
        def f_FormattedValue(): x = f"{var}"
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(internal.get_function_def(f_FormattedValue))

    def test_JoinedStr(self):
        def f_JoinedStr(): x = f"blah"
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(internal.get_function_def(f_JoinedStr))

    def test_Starred(self):
        starred_str = "*b = it"
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(ast.parse(starred_str))

    def test_Slice(self):
        def f_Slice(): x = mylist[1:2]
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(internal.get_function_def(f_Slice))

        # These tests are for nodes that are supported, but certain attributes are forbidden

    def test_Decorator(self):
        def f_decorators():
            @mydecorator
            def myfunc(): pass
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(internal.get_function_def(f_decorators))

    def test_Posonlyargs(self):
        def f_posonlyargs():
            def myfunc(a, /, b): pass
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(internal.get_function_def(f_posonlyargs))

    def test_Kwonlyargs(self):
        def f_kwonlyargs():
            def myfunc(a, *, b): pass
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(internal.get_function_def(f_kwonlyargs))

    def test_Starargs(self):
        def f_starargs():
            def myfunc(*args): pass
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(internal.get_function_def(f_starargs))

    def test_Kwstarargs(self):
        def f_kwstarargs():
            def myfunc(**kwargs): pass
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(internal.get_function_def(f_kwstarargs))

    def test_defaultargs(self):
        def f_defaultargs():
            def myfunc(a=1): pass
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(internal.get_function_def(f_defaultargs))

    def test_kwargscall(self):
        def f_kwargscall():
            x = myfunc(a = 1)
        with self.assertRaises(NotImplementedError): gamehop.filterast.filter_AST(internal.get_function_def(f_kwargscall))
