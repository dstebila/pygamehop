import ast
import copy
import secrets
from typing import cast, List, Optional, Union

from ...inlining import internal

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

class FindVariableDependencies(ast.NodeVisitor):
    """Find all the variables a node depends on."""
    def __init__(self):
        self.loads = list()
        self.stores = list()
    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load) and node.id not in self.loads: self.loads.append(node.id)
        if isinstance(node.ctx, ast.Store) and node.id not in self.stores: self.stores.append(node.id)

def contains_name(node: Union[ast.AST, List], name: str) -> bool:
    """Determines whether the given node (or list of nodes) contains a variable with the given name."""
    if isinstance(node, ast.AST): searchin = [node]
    else: searchin = node
    for element in searchin:
        var_deps = FindVariableDependencies()
        var_deps.visit(element)
        if name in var_deps.stores or name in var_deps.loads: return True
    return False

class NameNodeReplacer(ast.NodeTransformer):
    def __init__(self, id, replacement):
        self.id = id
        self.replacement = replacement
    def visit_Name(self, node):
        if node.id == self.id: return self.replacement
        else: return node

def collapse_useless_assigns(f: ast.FunctionDef) -> None:
    """Modify (in place) the given function definition to remove all lines containing tautological/useless assignments. For example, if the code contains a line "x = a" followed by a line "y = x + b", it replaces all subsequent instances of x with a, yielding the single line "y = a + b", up until x is set in another assignment statement.  Handles tuples.  Doesn't handle any kind of logic involving if statements or loops."""
    # keep looping until nothing changes
    keep_going = True
    while keep_going:
        keep_going = False
        for i in range(len(f.body)):
            stmt = f.body[i]
            if isinstance(stmt, ast.Assign):
                # assignment of the form x = a or x = 7 or x = (a, b)
                if isinstance(stmt.targets[0], ast.Name) and (isinstance(stmt.value, ast.Name) or isinstance(stmt.value, ast.Constant) or isinstance(stmt.value, ast.Tuple)):
                    replacer = NameNodeReplacer(stmt.targets[0].id, stmt.value)
                    # go through all subsequent statements and replace x with a until x is set anew
                    for j in range(i + 1, len(f.body)):
                        stmtprime = f.body[j]
                        if isinstance(stmtprime, ast.Assign):
                            # replace arg with val in the right hand side
                            stmtprime.value = replacer.visit(stmtprime.value)
                            # stop if arg is in the left
                            if contains_name(stmtprime.targets, replacer.id): break
                        else:
                            # replace arg with val in whole statement
                            f.body[j] = replacer.visit(stmtprime)
                    # remove the statement from the body
                    del f.body[i]
                    # we made a change, so loop again
                    keep_going = True
                    break
                # assignment of the form (x, y) = (a, b)
                elif isinstance(stmt.targets[0], ast.Tuple) and isinstance(stmt.value, ast.Tuple):
                    # make sure the lengths match
                    if len(stmt.targets[0].elts) != len(stmt.value.elts): break
                    break_out = False
                    # make sure everything on the left is just a name
                    for l in range(len(stmt.targets[0].elts)):
                        if not isinstance(stmt.targets[0].elts[l], ast.Name): break_out = True
                    if break_out: break
                    # expand (x, y) = (a, b) into tmpvar1 = a; tmpvar2 = b; x = tmpvar1; y = tmpvar2
                    # this should avoid problems like the following:
                    #     (x, y) = (f(x), g(x))
                    # is not equivalent to
                    #   x = f(x)
                    #   y = g(x)
                    # but is equivalent to
                    #   tmpvar1 = f(x)
                    #   tmpvar2 = g(x)
                    #   x = tmpvar1
                    #   y = tmpvar2
                    newstmts_tmps_store = list()
                    newstmts_tmps_load = list()
                    tmpvar_formatstr = 'v_' + secrets.token_hex(10) + '_{:d}'
                    for l in range(len(stmt.targets[0].elts)):
                        newstmts_tmps_store.append(
                            ast.Assign(
                                targets=[ast.Name(id=tmpvar_formatstr.format(l), ctx=ast.Store())],
                                value=stmt.value.elts[l]
                            )
                        )
                        newstmts_tmps_load.append(
                            ast.Assign(
                                targets=[stmt.targets[0].elts[l]],
                                value=ast.Name(id=tmpvar_formatstr.format(l), ctx=ast.Load())
                            )
                        )
                    # the new body should be everything before the current statement, 
                    # followed by all the tmpvar = ... assigns, 
                    # followed by all the ... = tmpvar assigns, 
                    # followed by everything after the current statement
                    new_f_body = list()
                    new_f_body.extend(f.body[:i])
                    new_f_body.extend(newstmts_tmps_store)
                    new_f_body.extend(newstmts_tmps_load)
                    new_f_body.extend(f.body[i+1:])
                    f.body = new_f_body
                    # we made a change, so loop again
                    keep_going = True
                    break
            elif isinstance(stmt, ast.If): raise NotImplementedError("Cannot handle functions with if statements.")
            elif isinstance(stmt, ast.For) or isinstance(stmt, ast.While): raise NotImplementedError("Cannot handle functions with loops.")
    ast.fix_missing_locations(f)

class LinkedList(object):
    def __init__(self):
        self.value: List[ast.AST] = list()
        self.children: Optional[LinkedList] = None
    def flatten(self):
        if self.children is not None: 
            return dict({'value': [ast.unparse(x) for x in self.value], 'children': self.children.flatten()})
        else:
            return dict({'value': [ast.unparse(x) for x in self.value]})

def assignee_vars(stmt: ast.Assign) -> List[str]:
    if len(stmt.targets) != 1: raise NotImplementedError("Cannot handle assignment statements with multiple targets")
    if isinstance(stmt.targets[0], ast.Name): return [stmt.targets[0].id]
    elif isinstance(stmt.targets[0], ast.Tuple): 
        ret = list()
        for x in stmt.targets[0].elts:
            if not isinstance(x, ast.Name): raise NotImplementedError("Cannot handle tuples containing things other than variables")
            ret.append(x.id)
        return ret
    else: raise NotImplementedError("Cannot handle assignments with left sides of the type " + str(type(stmt.targets[0]).__name__))

def dependent_vars(stmt: ast.Assign) -> List[str]:
    class FindLoadNames(ast.NodeVisitor):
        def __init__(self):
            self.found = list()
        def visit_Name(self, node):
            if isinstance(node.ctx, ast.Load): self.found.append(node.id)
    finder = FindLoadNames()
    finder.visit(stmt.value)
    return finder.found

def recurse(active_vars: List[str], body: List[ast.AST]) -> Optional[LinkedList]:
    """Given a list of variables currently active and a list of statements representing the body of the function,
    return a tree where the root of the tree is a list of independent statements that directly affect the active variables,
    TODO"""
    mytree = LinkedList()
    if len(body) == 0 or len(active_vars) == 0: return None
    new_body = copy.deepcopy(body)
    curr_active_vars = copy.deepcopy(active_vars)
    next_active_vars = list()
    for j in range(len(new_body) - 1, -1, -1):
        stmt = new_body[j]
        if not isinstance(stmt, ast.Assign): raise NotImplementedError("Don't know how to handle statements of type " + str(type(stmt).__name__))
        stmt_assignees = assignee_vars(stmt)
        # statement does not affect currently active variables so we don't need it
        if len(set(stmt_assignees) & set(curr_active_vars)) == 0: 
            del new_body[j]
            continue
        # statement affects only currently active variables, so we collect it at this level, and deactivate those variables
        elif len(set(stmt_assignees) & set(curr_active_vars)) == len(set(stmt_assignees)):
            mytree.value.append(stmt)
            del new_body[j]
            for v in stmt_assignees:
                if v in curr_active_vars: curr_active_vars.remove(v)
            next_active_vars.extend(dependent_vars(stmt))
        # some of the variables affected by this statement are currently active, but some are not
        else:
            not_curr_active = set(stmt_assignees) - set(curr_active_vars)
            # if the not active variables in this statement have no overlap with the active variables we started out with,
            # then we can collect this statement at this level, and deactivate those variables
            if len(not_curr_active & set(active_vars)) == 0:
                mytree.value.append(stmt)
                del new_body[j]
                for v in stmt_assignees:
                    if v in curr_active_vars: curr_active_vars.remove(v)
                next_active_vars.extend(dependent_vars(stmt))
            # if some of the variables in this statement overlap with the active variables we started out with, 
            # (but have already collected statements for at this level), then this statement is not for this level
            # remove all of this statement's assignees from the list of currently active variables
            else:
                for v in stmt_assignees:
                    if v in curr_active_vars: 
                        curr_active_vars.remove(v)
                        next_active_vars.append(v)
        if len(curr_active_vars) == 0: break
    # sort the lines at this level based on their variables order of appearance in active_vars
    mytree_value_new: List[ast.AST] = list()
    for v in active_vars:
        for stmt in mytree.value:
            assert isinstance(stmt, ast.Assign)
            if v in assignee_vars(stmt):
                mytree.value.remove(stmt)
                mytree_value_new.append(stmt)
                break
    assert len(mytree.value) == 0
    mytree.value = mytree_value_new
    mytree.children = recurse(next_active_vars, new_body)
    return mytree

def doit(f: ast.FunctionDef) -> Optional[LinkedList]:
    body = copy.deepcopy(f.body)
    # make sure the final statement is a return
    final_stmt = body[-1]
    del body[-1]
    stmts_at_level: List[List[ast.AST]] = list()
    if not isinstance(final_stmt, ast.Return): return None
    val = final_stmt.value
    if isinstance(final_stmt.value, ast.Constant): 
        ret = LinkedList()
        ret.value = [final_stmt]
        return ret
    elif not isinstance(final_stmt.value, ast.Name): raise NotImplementedError("Cannot handle functions with return type " + str(type(final_stmt.value).__name__))
    return_variable = final_stmt.value.id
    mytree = LinkedList()
    mytree.value = [final_stmt]
    mytree.children = recurse([return_variable], cast(List[ast.AST], body))
    return mytree

def canonicalize_line_order(f: ast.FunctionDef) -> None:
    mytree = doit(f)
    newbody: List[ast.AST] = list()
    while mytree != None:
        assert mytree is not None
        newbody = mytree.value + newbody
        mytree = mytree.children
    f.body = cast(List[ast.stmt], newbody)
    ast.fix_missing_locations(f)

def canonicalize_argument_order(f: ast.FunctionDef) -> None:
    body = copy.deepcopy(f.body)
    # make sure the final statement is a return
    final_stmt = body[-1]
    del body[-1]
    stmts_at_level: List[List[ast.AST]] = list()
    if not isinstance(final_stmt, ast.Return): return None
    # get the return value
    val = final_stmt.value
    if not isinstance(final_stmt.value, ast.Name): raise NotImplementedError("Cannot handle functions with return type " + str(type(final_stmt.value).__name__))
    active_vars = [final_stmt.value.id]
    # go through the statements starting from the end and accumulate the variables in order
    for i in range(len(body)-1, -1, -1):
        stmt = body[i]
        if not isinstance(stmt, ast.Assign): raise NotImplementedError("Cannot handle non-assign statements ({:s}) in {:s}".format(ast.unparse(stmt), f.name))
        dep_vars = dependent_vars(stmt)
        ass_vars = assignee_vars(stmt)
        if len(set(active_vars) & set(ass_vars)) != 0:
            active_vars.extend(dep_vars)
    # assemble the new list of arguments in order
    new_args = []
    vars_used = [] # since active_vars may contain some variables more than once, need to keep track of the ones we've already used
    for v in active_vars:
        for a in f.args.args:
            if a.arg == v and v not in vars_used:
                new_args.append(a)
                vars_used.append(v)
    f.args.args = new_args
    ast.fix_missing_locations(f)
