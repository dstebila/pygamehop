import ast
import copy

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
