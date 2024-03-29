import ast
import copy
from ... import utils
from typing import List
from ... import filterast
from ... import node_traverser as nt


def if_statements_to_expressions(f: ast.FunctionDef ) -> None:
    """Modify, in place, f so that all if statements become if expressions like so:
    if condition:
        v = expression1
    else:
        v = expression2

    becomes:

    v_if = expression1
    v_else = expression2
    v = v_if if condition else v_else

    Limitations:
    The resulting code will only be correct if there are no side effects in the body or orelse.  Also, the resulting
    code may not be safe to run, for example

    if x >= 0:
        v = math.sqrt(x)

    will result in

    v_if = math.sqrt(x)
    v_else = None
    v = v_if if x >= 0 else v_else

    so that now the math.sqrt(x) is run even if x < 0, resulting in an exception.
    """
    filterast.filter_AST(f.body, noifs=False)
    iftransformer = IfTransformer()
    iftransformer.visit_statements(f.body)
    ast.fix_missing_locations(f)
    filterast.filter_AST(f.body, noifs=True)

class IfTransformer(nt.NodeTraverser):
    def __init__(self):
        self.replacement_count = 0
        super().__init__()

    def visit_If(self, node: ast.If):
        # first fix up the bodies
        self.visit_statements(node.body)
        self.visit_statements(node.orelse)

        # find all the variables written to in the bodies
        body_stored_vars = utils.stored_vars(node.body)
        orelse_stored_vars = utils.stored_vars(node.orelse)
        all_stored_vars = list()
        for var in body_stored_vars: all_stored_vars.append(var)
        for var in orelse_stored_vars:
            if var not in all_stored_vars: all_stored_vars.append(var)

        # prefix all variables in the bodies so that they don't conflict
        body_prefix = "body_{:d}_".format(self.replacement_count)
        orelse_prefix = "orelse_{:d}_".format(self.replacement_count)
        newnodes = []
        newnodes.extend(utils.prefix_names(node.body, body_prefix))
        newnodes.extend(utils.prefix_names(node.orelse, orelse_prefix))

        # if one of the bodies doesn't assign to a variable that the other does, fix this
        for v in all_stored_vars:
            if v not in body_stored_vars:
                newnodes.append(ast.Assign(targets=[ast.Name(id=body_prefix + v, ctx=ast.Store())], value=ast.Constant(None)))
            if v not in orelse_stored_vars:
                newnodes.append(ast.Assign(targets=[ast.Name(id=orelse_prefix + v, ctx=ast.Store())], value=ast.Constant(None)))

        # choose if or else body variables based on node.test
        if len(all_stored_vars) == 1:
            newnodes.append(
                ast.Assign(
                    targets=[ast.Name(id=all_stored_vars[0], ctx=ast.Store())],
                    value=ast.IfExp(
                        test=node.test,
                        body=ast.Name(id=body_prefix + all_stored_vars[0], ctx=ast.Load()),
                        orelse=ast.Name(id=orelse_prefix + all_stored_vars[0], ctx=ast.Load())
                    )
                )
            )
        else:
            ifcondvar = "ifcond_{:d}".format(self.replacement_count)
            newnodes.append(ast.Assign(
                targets=[ast.Name(id=ifcondvar, ctx=ast.Store())],
                value=node.test
            ))
            for var in all_stored_vars:
                newnodes.append(
                    ast.Assign(
                        targets=[ast.Name(id=var, ctx=ast.Store())],
                        value=ast.IfExp(
                            test=ast.Name(id=ifcondvar, ctx=ast.Load()),
                            body=ast.Name(id=body_prefix + var, ctx=ast.Load()),
                            orelse=ast.Name(id=orelse_prefix + var, ctx=ast.Load())
                        )
                    )
                )

        self.replacement_count += 1
        return newnodes
