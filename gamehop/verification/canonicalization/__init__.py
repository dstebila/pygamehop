import ast
import copy
import secrets
from typing import cast, Dict, List, Optional, Union
import matplotlib.pyplot
import networkx

from ...inlining import internal
from ... import utils
from ... import node_traverser as nt

def canonicalize_function_name(f: ast.FunctionDef, name = 'f') -> None:
    """Modify (in place) the given function definition to have a canonical name."""
    f.name = name
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
    utils.rename_function_body_variables(f, mappings_1stpass)
    utils.rename_function_body_variables(f, mappings_2ndpass)
    ast.fix_missing_locations(f)

# apparently not used
def contains_name(node: Union[ast.AST, List], name: str) -> bool:
    """Determines whether the given node (or list of nodes) contains a variable with the given name."""
    return any( True for n in nt.nodes(node, nodetype = ast.Name) if n.id == name )

class VariableCollapser(nt.NodeTraverser):
    def visit_Name(self, node):
        node = self.generic_visit(node)
        if not isinstance(node.ctx, ast.Load):
            return node

        if not self.in_scope(node.id):   # this includes cases like function names
            return node

        value = self.var_value(node.id)

        if isinstance(value, ast.Constant) or isinstance(value, ast.Name) or isinstance(value, ast.Tuple):
            return value

        return node

def collapse_useless_assigns(f: ast.FunctionDef) -> None:
    """Modify (in place) the given function definition to remove all lines containing tautological/useless assignments. For example, if the code contains a line "x = a" followed by a line "y = x + b", it replaces all subsequent instances of x with a, yielding the single line "y = a + b", up until x is set in another assignment statement.  Handles tuples.  Doesn't handle any kind of logic involving if statements or loops."""

    VariableCollapser().visit(f)
    ast.fix_missing_locations(f)

# apparently not used
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



# generate a graph of the lines of the function
def function_to_graph(t: ast.FunctionDef):
    G = networkx.DiGraph()
    last_stmt_that_assigned_var: Dict[str, ast.AST] = dict() # keep track of the last statement that assigned to each variable
    # go through the lines of the statement in order
    for stmt in t.body:
        # add this statement to the graph as a node
        G.add_node(stmt)
        # add directed edges from this node to the last statement that assigned to each of its dependencies
        for v in utils.vars_depends_on(stmt):
            if v in last_stmt_that_assigned_var:
                G.add_edge(stmt, last_stmt_that_assigned_var[v])
        # record that this statement was the last statement to assign to each variable it assigned to
        for v in utils.vars_assigns_to(stmt):
            last_stmt_that_assigned_var[v] = stmt
    # we should now have a directed acyclic graph
    assert networkx.algorithms.dag.is_directed_acyclic_graph(G)
    return G

# find all the nodes that the return statement depends on
# (assumes that the return statement is the last statement in the function body)
def remove_irrelvant_nodes(G, f):
    assert isinstance(f.body[-1], ast.Return)
    return_stmt = f.body[-1]
    relevant_nodes = networkx.algorithms.dag.descendants(G, return_stmt) | {return_stmt}
    # remove all nodes that don't contribute to the return statement
    return G.subgraph(relevant_nodes).copy()

def canonicalize_line_order(f: ast.FunctionDef) -> None:
    """Modify (in place) the given function definition to canonicalize the order of lines
    based on the order in which the returned variable depends on previous lines. Lines
    that do not affect the return variable are removed.  Assumes that the return statement
    is the last statement in the function body"""
    G = function_to_graph(f)
    G = remove_irrelvant_nodes(G, f)
    # algorithm idea is as follows:
    # 0. add the return statement to the output list
    # 1. start from the return statement; call it the current node
    # 2. get the neighbours of the current node (i.e., the statements that most recently set the variables this statement depends on)
    # 3. remove this node from the graph
    # 4. remove from the list of neighbours any statements that still have other dependencies beyond this node
    # 5. order the remaining neighbours of the current node by the order in which the variables they set appear in the list of variables the current statement depends on
    # 6. add this statement's neighbours to the output list, if they haven't already been output
    # 7. add all of this statement's neighbours to the list of nodes to be processed, if they aren't already there
    # 8. set the current node to be the next node in the list of nodes to be processed, then go to step 2
    # 9. once there are no more nodes to be processed, output the output list in reverse order (so that the return statement is at the end)
    assert isinstance(f.body[-1], ast.Return)
    return_stmt = f.body[-1]
    ret = [return_stmt]
    left_to_process = [return_stmt]
    while len(left_to_process) > 0:
        curr_node = left_to_process[0]
        left_to_process = left_to_process[1:]
        if not G.has_node(curr_node): continue
        neighbors = list(G.neighbors(curr_node))
        G.remove_node(curr_node)
        filteredneighbors = list(filter(lambda n: G.in_degree(n) == 0, neighbors))
        def keyfn(k):
            for v in utils.vars_assigns_to(k):
                if v in utils.vars_depends_on(curr_node): return -utils.vars_depends_on(curr_node).index(v)
            return 0
        filteredneighbors.sort(key=keyfn)
        for n in filteredneighbors:
            if n not in ret:
                ret.append(n)
            if n not in left_to_process:
                left_to_process.append(n)
    f.body = list(reversed(ret))

def show_call_graph(f: ast.FunctionDef) -> None:
    G = function_to_graph(f)
    pos = networkx.shell_layout(G)
    networkx.draw(G, pos=pos, with_labels=True)
    matplotlib.pyplot.show()

class ArgumentReorderer(nt.NodeTraverser):
    def visit_FunctionDef(self, node):
        # visit the body to get the scope set up
        node = self.generic_visit(node)
        s = self.local_scope()
        node.args.args = [ ast.arg(arg = a, annotation = s.var_annotations[a]) for a in s.parameters_loaded ]
        return node

def canonicalize_argument_order(f: ast.FunctionDef) -> None:
    """Modify (in place) the given function definition to canonicalize the order of the arguments
    based on the order in which the variables appear.  Arguments that are not referred to are removed.
    Note that this also applies to any inner functions."""

    ArgumentReorderer().visit(f)
    ast.fix_missing_locations(f)

class LambdaReplacer(nt.NodeTraverser):
    def visit_Call(self, node):
        node = self.generic_visit(node)
        if not isinstance(node.func, ast.Name): return node
        if not self.in_scope(node.func.id): return node
        lam = self.var_value(node.func.id)
        if not isinstance(lam, ast.Lambda): return node

        lamargs = lam.args.args
        callargs = node.args
        assert len(lamargs) == len(callargs)
        lambody = copy.deepcopy(lam.body)
        mappings = dict()
        for i in range(len(lamargs)):
            mappings[lamargs[i].arg] = callargs[i]
        return utils.NameNodeReplacer(mappings).visit(lambody)


def inline_lambdas(f: ast.FunctionDef) -> None:
    """Modify (in place) the given function definition to replace all calls to lambdas with their body."""
    f = LambdaReplacer().visit(f)
    ast.fix_missing_locations(f)
