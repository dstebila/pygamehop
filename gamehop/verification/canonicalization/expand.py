import ast
import copy

from typing import Dict, List

from ...inlining import internal

class ExtractCallArguments(ast.NodeTransformer):
    """For every call node, if any of its arguments are not a constant or a variable
    name, extract that argument into a new assign statement to a temporary variable.
    The new assign statements are logged in the self.predecessors member. 
    Temporary variables names will be assigned starting at counter, and the counter 
    will be updated as new variables are added. The inner most arguments will be 
    extracted first."""
    def __init__(self, counter):
        self.predecessors = []
        self.counter = counter
    def visit_Call(self, node):
        newnode = copy.deepcopy(node)
        if len(newnode.keywords) > 0: raise NotImplementedError("Cannot handle calls with keywords")
        # go through each argument
        for i in range(len(newnode.args)):
            arg = newnode.args[i]
            # no changes needed for arguments that are a constant or a variable name
            if isinstance(arg, ast.Constant) or isinstance(arg, ast.Name): pass
            else:
                # recurse on the argument and extract any of its non-trivial arguments
                recurser = ExtractCallArguments(self.counter)
                newarg = recurser.visit(arg)
                # save any of its non-trivial arguments to the predecessor list
                self.predecessors.extend(recurser.predecessors)
                # update the counter based on how many it extracted
                self.counter = recurser.counter
                # add an assign statement to predecessors, assigning this argument
                # to a temporary variable
                tmpvar = "φ{:d}".format(self.counter)
                self.counter += 1
                self.predecessors.append(ast.Assign(
                    targets=[ast.Name(id=tmpvar, ctx=ast.Store())],
                    value=newarg
                ))
                # replace the argument with the temporary variable
                newnode.args[i] = ast.Name(id=tmpvar, ctx=ast.Load())
        return newnode

def call_arguments(f: ast.FunctionDef) -> None:
    """Modify (in place) the given function definition so that all non-trivial 
    (not a constant, not a variable name) arguments to function calls appear as 
    intermediate assignments immediately preceding the function call."""
    counter = 0
    # go through each statement in the body
    # replace it with any extracted argument assignments, then the (possibly
    # simplified) statement itself 
    newbody = list()
    for stmt in f.body:
        extractor = ExtractCallArguments(counter)
        stmt = extractor.visit(stmt)
        counter = extractor.counter
        newbody.extend(extractor.predecessors)
        newbody.append(stmt)
    f.body = newbody
    ast.fix_missing_locations(f)

def variable_reassign(f: ast.FunctionDef) -> None:
    """Modify (in place) the given function definition so that every variable is
    assigned to only once. If a variable is reassigned, give it a new name based
    on a counter. Can only handle functions with assign and return statements."""
    # keep track of how many times each variable has appeared
    counts: Dict[str, int] = dict()
    # format variable name based on counts: x, xν1, xν2, ...
    def varname(var, counts):
        if var not in counts or counts[var] == 0: return var
        else: return "{:s}ν{:d}".format(var, counts[var])
    # build the new body by going through each statement
    # rename any variables that are used based on what their current numbering
    # then update the count for any variables that have been reassigned
    newbody: List[ast.stmt] = list()
    for stmt in f.body:
        # construct the current list of variable renamings
        mappings = dict()
        for var in counts: 
            if counts[var] > 0: mappings[var] = varname(var, counts)
        renamer = internal.NameRenamer(mappings, True)
        # assign statements are the main thing to deal with
        if isinstance(stmt, ast.Assign):
            # rename all the variables on the RHS based on the current renamings
            stmt.value = renamer.visit(stmt.value)
            # increment the count for any variables that are reassigned
            for target in stmt.targets:
                # if assigning to a variable
                if isinstance(target, ast.Name):
                    # update the count depending on whether this is the first use
                    # or a reassignment
                    if target.id not in counts: counts[target.id] = 0
                    else: counts[target.id] += 1
                    # rename the variable if it's a reassignment
                    target.id = varname(target.id, counts)
                # if assigning to a tuple, go through every element in the tuple
                # and apply the same logic as the single-variable case in the if
                # branch above
                elif isinstance(target, ast.Tuple):
                    for elt in target.elts:
                        if isinstance(elt, ast.Name):
                            if elt.id not in counts: counts[elt.id] = 0
                            else: counts[elt.id] += 1
                            elt.id = varname(elt.id, counts)
                        else: raise NotImplementedError("Cannot handle tuples of things other than variables")
                else: raise NotImplementedError("Cannot handle assignments to things other than single variables or tuples")
            # add this statement to the output
            newbody.append(stmt)
        # for return statements, just rename all the variables it uses based on the current renamings
        elif isinstance(stmt, ast.Return):
            newstmt = renamer.visit(stmt)
            newbody.append(newstmt)
        else: raise NotImplementedError("Cannot handle statements other than assign and return")
    f.body = newbody
    ast.fix_missing_locations(f)
