import ast
import copy
import inspect
import types
from typing import cast, Any, Callable, List, Union, Tuple, Type

from . import internal
from .. import utils
from ..primitives import Crypto

__all__ = ['inline_argument_into_function', 'inline_function_call', 'inline_all_method_calls']

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

def inline_function_helper_lines_of_inlined_function(prefix: str, call: ast.Call, inlinand_def: ast.FunctionDef, self_prefix="") -> list:
    """Gets the lines of the body that result from expanding the call to 'call', with every local variable prefixed by prefix. If self_prefix is specified, variables starting with SELF will be renamed using self_prefix instead of prefix."""
    newinlinand_def = copy.deepcopy(inlinand_def)
    variables_in_inlinand = internal.find_all_variables(inlinand_def)
    # prefix all variables in inlinand
    mappings = dict()
    for var in variables_in_inlinand:
        if self_prefix != "" and var.startswith('SELF'):
            mappings[var] = '{:s}ⴰ{:s}'.format(self_prefix, var[4:])
        else:
            mappings[var] = '{:s}ⴰ{:s}'.format(prefix, var)
    newinlinand_def = utils.rename_variables(newinlinand_def, mappings)
    # the above might miss instances of SELFwhatever in places other than assigns, so we rename them everywhere
    class SELFRename(ast.NodeTransformer):
        def __init__(self, self_prefix):
            self.self_prefix = self_prefix
        def visit_Name(self, node):
            if node.id.startswith('SELF'):
                return ast.Name(id='{:s}ⴰ{:s}'.format(self_prefix, node.id[4:]), ctx=node.ctx)
            else: return node
    newinlinand_def = SELFRename(self_prefix).visit(newinlinand_def)
    # map the parameters onto the arguments
    assert len(call.args) == len(newinlinand_def.args.args)
    for i in range(len(call.args)):
        arg = call.args[i]
        if isinstance(arg, ast.Name):
            mapping = {newinlinand_def.args.args[i].arg: arg.id}
            newinlinand_def = utils.rename_variables(newinlinand_def, mapping, error_if_exists = False)
        elif isinstance(arg, ast.Constant):
            newinlinand_def = utils.get_function_def(inline_argument_into_function(newinlinand_def.args.args[i].arg, arg.value, newinlinand_def))
        else: raise NotImplementedError("Don't know how to inline calls whose arguments are of type {:s}".format(type(arg).__name__))
    return newinlinand_def.body




### OBSOLETE; TO BE DELETED
def inline_function_into_statements(inlinee: List[ast.stmt], inlinand: ast.FunctionDef, search_function_name, dest_function_name,  self_prefix="", replacements=0) -> Tuple[List[ast.stmt], int]:
    # get the function definitions
    inlinee_def = inlinee # copy.deepcopy(inlinee)
    inlinand_def = inlinand #copy.deepcopy(inlinand)

    # check that there are no return statements anywhere in the inlinand other than the last line
    class ContainsReturn(ast.NodeVisitor):
        def visit_Return(self, node):
            raise NotImplementedError("Function to be inlined ({:s}) has a return statement somewhere other than the last line".format(inlinand_def.name))
    for stmt in inlinand_def.body[:-1]:
        ContainsReturn().visit(stmt)

    # check if the last line of the inlinand is a return statement,
    inlinand_has_return = isinstance(inlinand_def.body[-1], ast.Return)
    
    # go through every line of the inlinee and replace all calls that we know how to handle
    newinlinee = []
    replacement_count = replacements
    for stmt in inlinee_def:
        # replace y = f(x)
        if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call) and isinstance(stmt.value.func, ast.Name) and stmt.value.func.id == search_function_name:
            if not inlinand_has_return: raise ValueError("Trying to inline a function ({:s}) without a return statement into an assignment".format(inlinand_def.name))
            # copy the expanded lines
            replacement_count += 1
            newinlinee.extend(inline_function_helper_lines_of_inlined_function('{:s}ᴠ{:d}'.format(dest_function_name, replacement_count), stmt.value, inlinand_def, self_prefix))
            # assign the required variables based on the return statement
            newinlinee[-1] = ast.Assign(
                targets = stmt.targets, value = newinlinee[-1].value
            )
        # replace f(x)
        elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call) and isinstance(stmt.value.func, ast.Name) and stmt.value.func.id == search_function_name:
            if inlinand_has_return: raise ValueError("Trying to inline a function with a return statement into a standalone statement")
            # copy the expanded lines
            replacement_count += 1
            newinlinee.extend(inline_function_helper_lines_of_inlined_function('{:s}ᴠ{:d}'.format(dest_function_name, replacement_count), stmt.value, inlinand_def, self_prefix))
        # recurse into if statements
        elif isinstance(stmt, ast.If):
            (stmt.body, replacement_count) = inline_function_into_statements(stmt.body, inlinand, search_function_name, dest_function_name, self_prefix, replacements=replacement_count)
            (stmt.orelse, replacement_count) = inline_function_into_statements(stmt.orelse, inlinand, search_function_name, dest_function_name, self_prefix, replacements=replacement_count)
            newinlinee.append(stmt)
        # recurse into function defs
        elif isinstance(stmt, ast.FunctionDef):
            (stmt.body, replacement_count) = inline_function_into_statements(stmt.body, inlinand, search_function_name, dest_function_name, self_prefix, replacements=replacement_count)
            newinlinee.append(stmt)
        else:
            newinlinee.append(stmt)

    # if there's still a call to our function somewhere, it must have been somewhere other than on a bare Assign line; raise an error
    class ContainsCall(ast.NodeVisitor):
        def __init__(self, funcname):
            self.funcname = funcname
        def visit_Call(self, node):
            if isinstance(node.func, ast.Name) and node.func.id == self.funcname:
                raise NotImplementedError("Can't inline functions that are called on anything other than as a solitary assignment line, e.g., y = f(x)")
    for stmt in newinlinee:
        ContainsCall(search_function_name).visit(stmt)
    return (newinlinee, replacement_count)

### OBSOLETE; TO BE DELETED
def inline_function(inlinee: Union[Callable, str, ast.FunctionDef], inlinand: Union[Callable, str, ast.FunctionDef], search_function_name=None, dest_function_name=None, self_prefix="") -> str:
    """Returns a string representing (almost) all instances of the second function inlined into the first.  Only works on calls to bare assignments (y = f(x)) or bare calls (f(x)). Normally uses the inlinand's name as the name to search for and the name from which to build prefixes, but can be overridden by search_function_name and dest_function_name. If self_prefix is specified, variables starting with SELF will be renamed using self_prefix instead of prefix."""
    # get the function definitions
    inlinee_def = copy.deepcopy(utils.get_function_def(inlinee))
    inlinand_def = copy.deepcopy(utils.get_function_def(inlinand))
    if search_function_name == None: search_function_name = inlinand_def.name
    if dest_function_name == None: dest_function_name = inlinand_def.name

    (inlinee_def.body, _ ) = inline_function_into_statements(inlinee_def.body, inlinand_def, search_function_name, dest_function_name, self_prefix)
    return ast.unparse(ast.fix_missing_locations(inlinee_def))

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
    # the last line is a return statement, strip that out to be just an expression
    assert isinstance(working_copy.body[-1], ast.Return)
    working_copy.body[-1] = ast.Expr(value=working_copy.body[-1].value)
    return working_copy.body

class InlineFunctionCallIntoStatements(utils.NewNodeTransformer):
    """Helper node transformer for inline_function_call. Does the actual replacement."""
    def __init__(self, f_to_be_inlined, f_dest_name):
        self.f_to_be_inlined = f_to_be_inlined
        self.fdef_to_be_inlined = utils.get_function_def(f_to_be_inlined)
        self.f_to_be_inlined_has_return = isinstance(self.fdef_to_be_inlined.body[-1], ast.Return)
        if isinstance(self.f_to_be_inlined, types.FunctionType):
            # methods of inner classes will have names like Blah.<locals>.Foo.Bar; this removes everything before Foo.Bar
            self.f_src_name = self.f_to_be_inlined.__qualname__.split('<locals>.')[-1]
        else: self.f_src_name = self.fdef_to_be_inlined.name
        self.f_dest_name = f_dest_name
        self.replacement_count = 0
    def visit_Assign(self, stmt):
        # replace y = f(x)
        if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call) and ast.unparse(stmt.value.func) == self.f_src_name:
            if not self.f_to_be_inlined_has_return:
                raise ValueError(f"Cannot inline function {self.fdef_to_be_inlined.name} into statement {ast.unparse(stmt)} in function {self.f_dest_name} since {self.fdef_to_be_inlined.name} does not return anything")
            # copy the expanded lines
            self.replacement_count += 1
            prefix = self.f_src_name.replace('.', '_')
            newlines = helper_make_lines_of_inlined_function(self.fdef_to_be_inlined, stmt.value.args, f'{prefix}ᴠ{self.replacement_count}')
            # assign the required variables based on the return statement
            assert isinstance(newlines[-1], ast.Expr)
            newlines[-1] = ast.Assign(targets = stmt.targets, value = newlines[-1].value)
            return newlines
        else: return stmt

def inline_function_call(f_to_be_inlined: Union[Callable, str, ast.FunctionDef], f_dest: Union[Callable, str, ast.FunctionDef]) -> str:
    """Returns a string representing the provided destination function with all calls to the function-to-be-inlined replaced with the body of that function, with arguments to the call appropriately bound and with local variables named unambiguously."""

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

    # check if the last line of f_to_be_inlined is a return statement,
    f_to_be_inlined_has_return = isinstance(fdef_to_be_inlined.body[-1], ast.Return)

    # go through every line of the inlinee and replace all calls that we know how to handle
    newdest = fdef_dest
    newdest.body = InlineFunctionCallIntoStatements(f_to_be_inlined, fdef_dest.name).visit(newdest.body)

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

### OBSOLETE; TO BE DELETED
def inline_class(inlinee: Union[Callable, str, ast.FunctionDef], arg: str, inlinand: Union[Type[Any], str, ast.ClassDef], inline_init = True, inline_class_props = True) -> str:
    """Returns a string representing the given class definition inlined into an argument of the given function.."""
    # get the function definitions
    inlinee_def = copy.deepcopy(utils.get_function_def(inlinee))
    inlinand_def = copy.deepcopy(utils.get_class_def(inlinand))
    # inline class properties
    class_props_to_add: List[ast.stmt] = []
    if inline_class_props:
        for stmt in inlinand_def.body:
            if isinstance(stmt, ast.Assign):
                assert(isinstance(stmt.targets[0], ast.Name))
                newvarname = '{:s}ⴰ{:s}'.format(arg, stmt.targets[0].id)
                class_props_to_add.append(
                    ast.Assign(
                        [ast.Name(id=newvarname, ctx=ast.Store())],
                        stmt.value
                    )
                )
    # inline the __init__ method
    init_stmts_to_add: List[ast.stmt] = []
    if inline_init:
        for f in inlinand_def.body:
            if isinstance(f, ast.FunctionDef) and f.name == '__init__':
                initdef = copy.deepcopy(f)
                # dereference self.whatever in __init__
                formatstr = '{:s}ⴰ'.format(arg) + '{:s}'
                selfname = initdef.args.args[0].arg
                initdef = utils.get_function_def(internal.dereference_attribute(initdef, selfname, formatstr))
                # rename any of __init__'s (non-self) parameters and add them to inlinee's list of arguments
                for a in initdef.args.args[1:]:
                    newname = '{:s}ⴰinitⴰ{:s}'.format(arg, a.arg)
                    initdef = utils.rename_variables(initdef, {a.arg: newname})
                    newarg = copy.deepcopy(a)
                    newarg.arg = newname
                    inlinee_def.args.args.append(newarg)
                # copy the body of __init__ to the start of the inlinee body
                init_stmts_to_add = initdef.body
    inlinee_def.body = class_props_to_add + init_stmts_to_add + inlinee_def.body
    # dereference attribute calls in the new body
    formatstr = '{:s}ⴰ'.format(arg) + '{:s}'
    inlinee_def = utils.get_function_def(internal.dereference_attribute(inlinee_def, arg, formatstr))
    # inline all remaining methods
    for f in inlinand_def.body:
        if isinstance(f, ast.FunctionDef) and f.name != '__init__':
            fdef = copy.deepcopy(f)
            # dereference self.whatever in the function
            formatstr = 'SELF{:s}'
            selfname = fdef.args.args[0].arg
            fdef = utils.get_function_def(internal.dereference_attribute(fdef, selfname, formatstr))
            del fdef.args.args[0]
            # inline the method; we've already done the prefixing so we tell inline_function not to add its own prefixes
            inlinee_def = utils.get_function_def(inline_function(inlinee_def, fdef, search_function_name='{:s}ⴰ{:s}'.format(arg, fdef.name), dest_function_name='{:s}ⴰ{:s}'.format(arg, fdef.name), self_prefix='{:s}'.format(arg)))
    # remove the inlined argument from the inlinee's list of argments
    newargs = list()
    for i in range(len(inlinee_def.args.args)):
        if inlinee_def.args.args[i].arg != arg:
            newargs.append(inlinee_def.args.args[i])
    inlinee_def.args.args = newargs
    return ast.unparse(ast.fix_missing_locations(inlinee_def))

def inline_all_method_calls(c_to_be_inlined: Union[Type[Any], str, ast.ClassDef], f_dest: Union[Callable, str, ast.FunctionDef]) -> str:
    """Returns a string representing the provided destination function with all calls to methods of the given class-to-be-inlined replaced with the body of that function, with arguments to the call appropriately bound and with local variables named unambiguously.  Only handles classes with static methods."""

    cdef_to_be_inlined = utils.get_class_def(c_to_be_inlined)
    fdef_dest = utils.get_function_def(f_dest)
    
    # go through every function 
    for f in cdef_to_be_inlined.body:
        if isinstance(f, ast.FunctionDef):
            # can't handle classes with non-static functions
            is_static_method = False
            for d in f.decorator_list:
                if isinstance(d, ast.Name) and d.id == 'staticmethod': is_static_method = True
            if not is_static_method:
                raise ValueError(f"Unable to inline non-static method {f.name} from class {cdef_to_be_inlined.name} into function {fdef_dest.name}")
            # hack the method's name to include the class name
            f.name = cdef_to_be_inlined.name + "." + f.name
            # inline calls to this method
            fdef_dest = utils.get_function_def(inline_function_call(f, fdef_dest))
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
            class SelfSchemeRenamer(ast.NodeTransformer):
                def visit_Attribute(self, node):
                    if isinstance(node.value, ast.Name) and node.value.id == 'self' and node.attr == 'Scheme':
                        return ast.Name(id=Scheme.__name__, ctx=node.ctx)
                    elif isinstance(node.value, ast.Attribute):
                        return ast.Attribute(value=self.visit_Attribute(node.value), attr=node.attr, ctx=node.ctx)
                        return ast.Name(id=Scheme.__name__, ctx=node.ctx)
                    else: return node
            fdef = SelfSchemeRenamer().visit(fdef)
            Game_newbody.append(utils.get_function_def(inline_all_method_calls(Scheme, cast(ast.FunctionDef, fdef))))
    Game_copy.body = Game_newbody
    return ast.unparse(ast.fix_missing_locations(Game_copy))
