import ast
import types
from typing import cast, Any, Callable, List, Optional, Type, Union

from .. import utils
from ..primitives import Crypto

__all__ = ['inline_argument_into_function', 'inline_function_call', 'inline_all_static_method_calls', 'inline_all_nonstatic_method_calls' 'inline_scheme_into_game', 'inline_reduction_into_game']

# Note that inlining uses Unicode symbols to make it look like the original code
# e.g. attribute dereferencing: x.y gets inlined to xⴰy
#      variables in an inlined function: def f(): a = y gets inlined to
#      fᴠ1ⴰa (here the ᴠ1 denotes it's the first inlining of this function)
# https://www.asmeurer.com/python-unicode-variable-names/

def inline_argument_into_function(argname: str, val: Union[bool, float, int, str, tuple, ast.expr, Type[Any]], f: Union[Callable, str, ast.FunctionDef]) -> str:
    """Returns a string representing the provided function with the given argument inlined to the given value.  Works on values of type bool, float, int, str, tuple, or an AST expression.  Cannot handle cases where the variable to be inlined is assigned to."""
    fdef = utils.get_function_def(f)
    # check that the argument is present
    if argname not in [a.arg for a in fdef.args.args]:
        raise KeyError(f"Argument {argname} not found in list of arguments to function {fdef.name}")
    # check that the argument is never assigned to
    if argname in utils.vars_assigns_to(fdef.body):
        raise ValueError(f"Error inlining argument {argname} into function {fdef.name}: {argname} is assigned to in the body of {fdef.name}")
    # construct the new node
    if isinstance(val, bool) or isinstance(val, float) or isinstance(val, int) or isinstance(val, str) or isinstance(val, tuple):
        def ast_from_literal(x: Union[bool, float, int, str, tuple]) -> ast.expr:
            if isinstance(x, bool) or isinstance(x, float) or isinstance(x, int) or isinstance(x, str):
                return ast.Constant(value=x)
            elif isinstance(x, tuple):
                return ast.Tuple(elts=[ast_from_literal(y) for y in x], ctx=ast.Load())
        newnode = ast_from_literal(val)
    elif isinstance(val, ast.expr): newnode = val
    elif isinstance(val, type): newnode = ast.Name(val.__name__, ast.Load())
    else: raise TypeError(f"Don't know how to inline objects of type {type(val).__name__}")
    newfdef = utils.NameNodeReplacer({argname: newnode}).visit(fdef)
    # remove the argument from the arguments list
    for a in newfdef.args.args:
        if a.arg == argname:
            newfdef.args.args.remove(a)
            break
    # return the resulting function
    return ast.unparse(ast.fix_missing_locations(newfdef))

def helper_make_lines_of_inlined_function(fdef_to_be_inlined: ast.FunctionDef, params: List[ast.expr], prefix: str) -> List[ast.stmt]:
    """Helper function for InlineFunctionCallIntoStatements. Takes a function definition and list of parameters (one for each argument of the function definition) and returns a copy of the body of the function in which (a) all local variables have been prefixed with prefix and (b) all instances of arguments have been replaced with the corresponding parameter."""
    working_copy = fdef_to_be_inlined
    # prefix all local variables
    local_variables = utils.vars_assigns_to(fdef_to_be_inlined.body)
    mappings = dict()
    for var in local_variables: mappings[var] = f"{prefix}ⴰ{var}"
    working_copy = utils.rename_variables(working_copy, mappings)
    # map the parameters onto the arguments
    assert len(params) == len(working_copy.args.args)
    replacements = {arg.arg: params[argnum] for argnum, arg in enumerate(working_copy.args.args)}
    working_copy = utils.NameNodeReplacer(replacements).visit(working_copy)
    # if the last line is a return statement, strip that out to be just an expression
    if isinstance(working_copy.body[-1], ast.Return):
        working_copy.body[-1] = ast.Expr(value=working_copy.body[-1].value)
    return working_copy.body

class InlineFunctionCallIntoStatements(utils.NewNodeTransformer):
    """Helper node transformer for inline_function_call. Does the actual replacement.  If the optional selfname argument is given, then the arguments list will be prepended with an argument corresponding to selfname."""
    def __init__(self, f_to_be_inlined, f_dest_name, selfname = None, f_to_be_inlined_name = None):
        self.f_to_be_inlined = f_to_be_inlined
        self.fdef_to_be_inlined = utils.get_function_def(f_to_be_inlined)
        self.f_to_be_inlined_has_return = isinstance(self.fdef_to_be_inlined.body[-1], ast.Return)
        if f_to_be_inlined_name == None:
            if isinstance(self.f_to_be_inlined, types.FunctionType):
                # methods of inner classes will have names like Blah.<locals>.Foo.Bar; this removes everything before Foo.Bar
                self.f_src_name = self.f_to_be_inlined.__qualname__.split('<locals>.')[-1]
            else: self.f_src_name = self.fdef_to_be_inlined.name
        else: self.f_src_name = f_to_be_inlined_name
        self.f_dest_name = f_dest_name
        self.selfname = selfname
        self.replacement_count = 0
    def visit_Assign(self, stmt):
        # replace y = f(x)
        if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call) and ast.unparse(stmt.value.func) == self.f_src_name:
            if not self.f_to_be_inlined_has_return:
                raise ValueError(f"Cannot inline function {self.fdef_to_be_inlined.name} into statement {ast.unparse(stmt)} in function {self.f_dest_name} since {self.fdef_to_be_inlined.name} does not return anything")
            # prepare the replacement
            self.replacement_count += 1
            prefix = self.f_src_name.replace('.', '_')
            # if selfname is provided, prepend the list of arguments with an argument based on selfname before doing the substitution
            if self.selfname == None: newargs = stmt.value.args
            else: newargs = [ast.arg(arg=self.selfname)] + stmt.value.args
            # copy the expanded lines
            newlines = helper_make_lines_of_inlined_function(self.fdef_to_be_inlined, newargs, f'{prefix}ᴠ{self.replacement_count}')
            # assign the required variables based on the return statement
            assert isinstance(newlines[-1], ast.Expr)
            newlines[-1] = ast.Assign(targets = stmt.targets, value = newlines[-1].value)
            return newlines
        else: return stmt
    def visit_Expr(self, stmt):
        # replace f(x)
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call) and ast.unparse(stmt.value.func) == self.f_src_name:
            # prepare the replacement
            self.replacement_count += 1
            prefix = self.f_src_name.replace('.', '_')
            # if selfname is provided, prepend the list of arguments with an argument based on selfname before doing the substitution
            if self.selfname == None: newargs = stmt.value.args
            else: newargs = [ast.arg(arg=self.selfname)] + stmt.value.args
            # copy the expanded lines
            newlines = helper_make_lines_of_inlined_function(self.fdef_to_be_inlined, newargs, f'{prefix}ᴠ{self.replacement_count}')
            return newlines
        else: return stmt

def inline_function_call(f_to_be_inlined: Union[Callable, str, ast.FunctionDef], f_dest: Union[Callable, str, ast.FunctionDef], selfname: Optional[str] = None, f_to_be_inlined_name: Optional[str] = None) -> str:
    """Returns a string representing the provided destination function with all calls to the function-to-be-inlined replaced with the body of that function, with arguments to the call appropriately bound and with local variables named unambiguously. If the optional selfname argument is given, then the arguments list will be prepended with an argument corresponding to selfname."""

    fdef_to_be_inlined = utils.get_function_def(f_to_be_inlined)
    fdef_dest = utils.get_function_def(f_dest)

    # check that there are no return statements anywhere in f_to_be_inlined other than the last line
    class ContainsReturn(ast.NodeVisitor):
        def __init__(self): self.found = False
        def visit_Return(self, node): self.found = True
    for lineno, stmt in enumerate(fdef_to_be_inlined.body[:-1]):
        contains_return = ContainsReturn()
        contains_return.visit(stmt)
        if contains_return.found == True:
            raise NotImplementedError(f"Inlining function {fdef_to_be_inlined.name} into {fdef_dest.name} since {fdef_to_be_inlined.name} contains a return statement somewhere other than the last line (namely, line {lineno+1})")

    # go through every line of the inlinee and replace all calls that we know how to handle
    newdest = fdef_dest
    newdest.body = InlineFunctionCallIntoStatements(f_to_be_inlined, fdef_dest.name, selfname=selfname, f_to_be_inlined_name=f_to_be_inlined_name).visit(newdest.body)

    # if there's still a call to our function somewhere, it must have been somewhere other than on a bare Assign line; raise an error
    class ContainsCall(utils.NewNodeVisitor):
        def __init__(self, funcname):
            self.funcname = funcname
            self.found = False
        def visit_Call(self, node):
            if isinstance(node.func, ast.Name) and node.func.id == self.funcname: self.found = True
    if isinstance(f_to_be_inlined, types.FunctionType): name = f_to_be_inlined.__qualname__.split("<locals>.")[-1] # methods of inner classes will have names like Blah.<locals>.Foo.Bar; this removes everything before Foo.Bar
    else: name = fdef_to_be_inlined.name
    contains_call = ContainsCall(name)
    contains_call.visit(newdest.body)
    if contains_call.found:
        raise ValueError(f"Could not fully inline {fdef_to_be_inlined.name} into {fdef_dest.name} since {fdef_dest.name} calls {fdef_to_be_inlined.name} in an unsupported way; the only supported way is an assignment statement of the form foo = {fdef_to_be_inlined.name}(bar)")

    return ast.unparse(ast.fix_missing_locations(newdest))

def is_static_functiondef(f: ast.FunctionDef) -> bool:
    """Helper function that recognizes static methods of a function def."""
    for d in f.decorator_list:
        if isinstance(d, ast.Name) and d.id == 'staticmethod': return True
    return False

def inline_all_nonstatic_method_calls(o_name: str, c_to_be_inlined: Union[Type[Any], str, ast.ClassDef], f_dest: Union[Callable, str, ast.FunctionDef]) -> str:
    """Returns a string representing the provided destination function with all calls to non-static methods of the given object replaced with the body of that function, with arguments to the call appropriately bound and with local variables named unambiguously."""
    cdef_to_be_inlined = utils.get_class_def(c_to_be_inlined)
    fdef_dest = utils.get_function_def(f_dest)
    # go through every function 
    for f in cdef_to_be_inlined.body:
        if isinstance(f, ast.FunctionDef):
            if is_static_functiondef(f): continue
            # hack the method's name to include the object name
            f.name = o_name + "." + f.name
            # inline calls to this method
            fdef_dest = utils.get_function_def(inline_function_call(f, fdef_dest, selfname=o_name))
    return ast.unparse(ast.fix_missing_locations(fdef_dest))

def inline_all_static_method_calls(c_to_be_inlined: Union[Type[Any], str, ast.ClassDef], f_dest: Union[Callable, str, ast.FunctionDef]) -> str:
    """Returns a string representing the provided destination function with all calls to static methods of the given class-to-be-inlined replaced with the body of that function, with arguments to the call appropriately bound and with local variables named unambiguously."""

    cdef_to_be_inlined = utils.get_class_def(c_to_be_inlined)
    fdef_dest = utils.get_function_def(f_dest)
    
    # go through every function 
    for f in cdef_to_be_inlined.body:
        if isinstance(f, ast.FunctionDef):
            # can't handle classes with non-static functions
            if not is_static_functiondef(f): continue
            # hack the method's name to include the class name
            f.name = cdef_to_be_inlined.name + "." + f.name
            # inline calls to this method
            fdef_dest = utils.get_function_def(inline_function_call(f, fdef_dest))
    return ast.unparse(ast.fix_missing_locations(fdef_dest))

def inline_all_inner_class_init_calls(c_to_be_inlined: Union[Type[Any], str, ast.ClassDef], f_dest: Union[Callable, str, ast.FunctionDef]) -> str:
    """Returns a string where calls to __init__ methods of inner classes of c_to_be_inlined are inlined into f_dest, with arguments to the call appropriately bound and with local variables named unambiguously."""

    cdef_to_be_inlined = utils.get_class_def(c_to_be_inlined)
    fdef_dest = utils.get_function_def(f_dest)
    
    class ReplaceInit(utils.NewNodeTransformer):
        def __init__(self, needle: str):
            self.needle = needle
        def visit_Assign(self, node):
            if isinstance(node.value, ast.Call) and ast.unparse(node.value.func) == self.needle:
                if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
                    raise ValueError(f"Left-hand side of assignment statements involving constructors must be a single variable {ast.unparse(node)}")
                # for example, suppose the statement is
                #     z = C.D(3, 2)
                # construct statements
                #     z = C.D.__new__(C.D)
                #     C.D.__init__(z, 3, 2)
                ret = []
                ret.append(ast.Assign(
                    targets = [node.targets[0]],
                    value = ast.Call(
                        func=ast.Attribute(
                            value=node.value.func,
                            attr='__new__',
                            ctx=ast.Load()
                        ),
                        args=[node.value.func],
                        keywords=[]
                    )
                ))
                ret.append(ast.Expr(
                    value = ast.Call(
                        func=ast.Attribute(
                            value=node.value.func,
                            attr='__init__',
                            ctx=ast.Load()
                        ),
                        args=[node.targets[0]] + node.value.args,
                        keywords=[]
                    )
                ))
                return ret
            return node
    
    # go through every inner class
    for innerc in cdef_to_be_inlined.body:
        if isinstance(innerc, ast.ClassDef):
            for method in innerc.body:
                if isinstance(method, ast.FunctionDef) and method.name == '__init__':
                    n = cdef_to_be_inlined.name + "." + innerc.name
                    # convert
                    #     z = C.D(3, 2)
                    # to
                    #     z = C.D.__new__(C.D)
                    #     C.D.__init__(z, 3, 2)
                    fdef_dest = ReplaceInit(n).visit(fdef_dest)
                    # then inline calls to C.D.__init__
                    fdef_dest = utils.get_function_def(inline_function_call(method, fdef_dest, f_to_be_inlined_name=n + ".__init__"))
    return ast.unparse(ast.fix_missing_locations(fdef_dest))

def inline_scheme_into_game(Scheme: Type[Crypto.Scheme], Game: Type[Crypto.Game]) -> str:
    """Returns a string representing the provided cryptographic game with all calls to methods of the given cryptographic scheme replaced with the body of those functions, with arguments to the call appropriately bound and with local variables named unambiguously."""
    Game_copy = utils.get_class_def(Game)
    Game_newbody: List[ast.stmt] = []
    # go through every method of the game (__init__, main, oracles)
    for fdef in Game_copy.body:
        # make sure the game only consists of functions
        if not isinstance(fdef, ast.FunctionDef):
            raise ValueError(f"Unable to handle games with members that are anything other than functions; game {Game_copy.name}, member {ast.unparse(fdef).splitlines()[0]}")
        # __init__ has a special form for games and must always consist of just two lines, setting self.Scheme and self.Adversary
        # bind self.Scheme to the given Scheme
        if fdef.name == "__init__":
            Game_newbody.append(utils.get_function_def(inline_argument_into_function('Scheme', Scheme, fdef)))
        else:
            # references to the scheme will look like "self.Scheme.whatever"
            # replace these with "Scheme.whatever" so that they can easily be replaced
            fdef = utils.AttributeNodeReplacer(['self', 'Scheme'], Scheme.__name__).visit(fdef)
            fdef = utils.get_function_def(inline_all_static_method_calls(Scheme, cast(ast.FunctionDef, fdef)))
            fdef = utils.get_function_def(inline_all_inner_class_init_calls(Scheme, cast(ast.FunctionDef, fdef)))
            Game_newbody.append(fdef)
    Game_copy.body = Game_newbody
    return ast.unparse(ast.fix_missing_locations(Game_copy))

def inline_reduction_into_game(R: Type[Crypto.Reduction], GameForR: Type[Crypto.Game], SchemeForR: Type[Crypto.Scheme], TargetGame: Type[Crypto.Game], TargetScheme: Type[Crypto.Scheme]) -> str:
    """Returns a string representing the inlining of a reduction into a game, to yield another game.  R is the reduction, which an adversary in the game GameForR against scheme SchemeForR.  The result of the inlining is a cryptographic game intended to be of the form TargetGame against scheme TargetScheme."""
    # The high-level idea of this procedure is as follows:
    # 1. The main method of the result should take the main method of the GameForR and inline all calls to R.
    # 2. R provides methods that will become oracles in the resulting game; these are copied from R.
    # 3. The body of all the oracles of GameForR will be inlined into the resulting game.
    # 4. Various things are renamed and minor things are changed, for example turning static methods into non-static methods.
    OutputGame = utils.get_class_def(TargetGame)
    OutputGame.body = []
    # copy the __init__ and main methods of GameForR into OutputGame
    GameForR_copy = utils.get_class_def(GameForR)
    # and save the oracles of GameForR that will need to be inlined into the OutputGame
    OraclesToSave: List[ast.FunctionDef] = []
    for fdef in GameForR_copy.body:
        # make sure the game only consists of functions
        if not isinstance(fdef, ast.FunctionDef):
            raise ValueError(f"Unable to handle games with members that are anything other than functions; game {GameForR_copy.name}, member {ast.unparse(fdef).splitlines()[0]}")
        if fdef.name == "__init__":
            # __init__ has a special form for games and must always consist of just two lines, setting self.Scheme and self.Adversary
            # bind self.Scheme to the given Scheme
            newinit = utils.get_function_def(inline_argument_into_function('Scheme', TargetScheme, fdef))
            # change the type of the adversary to match the target game
            newinit = utils.NameRenamer({f"{GameForR.__name__}_Adversary": f"{TargetGame.__name__}_Adversary"}, False).visit(newinit)
            OutputGame.body.append(newinit)
        elif fdef.name == "main" or fdef.name.startswith("o_"):
            if fdef.args.args[0].arg != "self":
                raise ValueError(f"First parameter of {fdef.name} is called '{fdef.args.args[0].arg}', should be called 'self'.")
            # inline self.adversary as R
            fdef = utils.AttributeNodeReplacer(['self', 'adversary'], R.__name__).visit(fdef)
            fdef = utils.get_function_def(inline_all_nonstatic_method_calls(R.__name__, R, cast(ast.FunctionDef, fdef)))
            # rename any of R's member variables to self
            fdef = utils.rename_variables(fdef, {R.__name__: 'self'}, False)
            # replace references to self.Scheme with the scheme that R was using
            fdef = utils.AttributeNodeReplacer(['self', 'Scheme'], SchemeForR.__name__).visit(fdef)
            # replace R's calls to its inner adversary with calls to the outer game's self.adversary
            fdef = utils.AttributeNodeReplacer(['self', 'inner_adversary'], 'self.adversary').visit(fdef)
            # GameForR's oracles will need to be saved
            assert isinstance(fdef, ast.FunctionDef) # needed for typechecker
            if fdef.name.startswith("o_"):
                OraclesToSave.append(fdef)
            else:
                OutputGame.body.append(fdef)
        else:
            raise ValueError(f"Method {fdef.name} in game {GameForR_copy.name} is an unknown type of method; only __init__, main, and oracles labeled o_ are allowed.")
    # copy all oracles of R into the output game
    R_copy = utils.get_class_def(R)
    for fdef in filter(lambda fdef: isinstance(fdef, ast.FunctionDef) and fdef.name.startswith("o_"), R_copy.body):
        assert isinstance(fdef, ast.FunctionDef) # needed for typechecker
        OutputGame.body.append(fdef)
    # for each oracle of GameForR that we saved, inline it into the OutputGame
    for fdef in OraclesToSave:
        # calls to this oracle in OutputGame will be of the form R.o_whatever
        # first we'll give those calls a temporary name
        OutputGame.body = utils.AttributeNodeReplacer(['self', 'i' + fdef.name], R.__name__ + '_i' + fdef.name).visit(OutputGame.body)
        # Stateful games that need to save a reference to their oracle will have had a line like
        #     self.io_whatever = o_whatever
        # By the line above, this will have been transformed into 
        #     R_io_whatever = self.o_whatever
        # This is now a redundant line, so we'll remove that
        class OracleSaverRemover(utils.NewNodeTransformer):
            def __init__(self, Rname: str, fdefname: str): 
                self.Rname = Rname
                self.fdefname = fdefname
            def visit_Assign(self, node: ast.Assign):
                if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id == self.Rname + '_i' + self.fdefname and ast.unparse(node.value) == 'self.' + self.fdefname:
                    return None
                else: return node
        OutputGame = OracleSaverRemover(R.__name__, fdef.name).visit(OutputGame)
        fdef.name = R.__name__ + '_i' + fdef.name
        # remove self from the function
        del fdef.args.args[0]
        # inline this function into every method of the OutputGame
        for i, otherfdef in enumerate(OutputGame.body):
            assert isinstance(otherfdef, ast.FunctionDef) # needed for typechecker
            OutputGame.body[i] = utils.get_function_def(inline_function_call(fdef, otherfdef))
    # go through every method of the game (__init__, main, oracles)
    for i, fdef in enumerate(OutputGame.body):
        # make sure the game only consists of functions
        if not isinstance(fdef, ast.FunctionDef):
            raise ValueError(f"Unable to handle games with members that are anything other than functions; game {OutputGame.name}, member {ast.unparse(fdef).splitlines()[0]}")
        # __init__ has a special form for games and must always consist of just two lines, setting self.Scheme and self.Adversary
        # bind self.Scheme to the given Scheme
        if fdef.name == "__init__": continue
        else:
            OutputGame.body[i] = utils.get_function_def(inline_all_inner_class_init_calls(TargetScheme, cast(ast.FunctionDef, fdef)))
    return ast.unparse(ast.fix_missing_locations(OutputGame))
