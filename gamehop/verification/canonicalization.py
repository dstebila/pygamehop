import ast
import secrets

from ..inlining import internal

def canonicalize_function_name(f: ast.FunctionDef, name = 'f') -> None:
    """Modify (in place) the given function definition to have a canonical name."""
    f.name = name
    ast.fix_missing_locations(f)

def canonicalize_return(f: ast.FunctionDef) -> None:
    """Modify (in place) the given function definition to simplify its return statement to be either a constant or a single variable."""
    class ReturnExpander(ast.NodeTransformer):
        def __init__(self, vars, prefix = 'ret'):
            self.vars = vars
            self.prefix = prefix
        def visit_Return(self, node):
            # if it directly returns a constant or variable, consider that canonical
            if isinstance(node.value, ast.Constant): return node
            if isinstance(node.value, ast.Name): return node
            # otherwise, make a new assignment for that return value and then return the newly assigned variable
            # find a unique name for the return value
            i = 0
            retname = '{:s}{:d}'.format(self.prefix, i)
            while retname in self.vars:
                i += 1
                retname = '{:s}{:d}'.format(self.prefix, i)
            self.vars.append(retname)
            assign = ast.Assign(
                targets = [ast.Name(id=retname, ctx=ast.Store())],
                value = node.value
            )
            ret = ast.Return(
                value = ast.Name(id=retname, ctx=ast.Load())
            )
            return [assign, ret]
    vars = internal.find_all_variables(f)
    fprime = ReturnExpander(vars).visit(f)
    f.body = fprime.body
    ast.fix_missing_locations(f)

def canonicalize_variable_names(f: ast.FunctionDef, prefix = 'v') -> None:
    """Modify (in place) the given function definition to give variables canonical names."""
    # first rename everything to a random string followed by a counter
    # then rename them to v0, v1, v2, ...
    tmpname = 'tmp_' + secrets.token_hex(10)
    # set up the mappings
    vars = internal.find_all_variables(f)
    mappings_1stpass = dict()
    mappings_2ndpass = dict()
    for i in range(len(vars)):
        mappings_1stpass[vars[i]] = '{:s}{:d}'.format(tmpname, i)
        mappings_2ndpass[mappings_1stpass[vars[i]]] = '{:s}{:d}'.format(prefix, i)
    # rename to temporary names, then output names
    f_1stpass = internal.rename_variables(f, mappings_1stpass)
    f_2ndpass = internal.rename_variables(f_1stpass, mappings_2ndpass)
    # save results in place
    f.args = f_2ndpass.args
    f.body = f_2ndpass.body
    ast.fix_missing_locations(f)
