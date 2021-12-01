import ast

from ... import node_traverser as nt
from ... import utils

class MembersUsedInMethod(nt.NodeTraverser):
    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        for d in node.decorator_list:
            if isinstance(d, ast.Name) and d.id == 'staticmethod': return []
        if len(node.args.args) == 0: return []
        selfname = node.args.args[0].arg
        s = self.local_scope()
        return [a for a in s.variables[selfname].attributes]

def unnecessary_members(c: ast.ClassDef) -> None:
    selfattributes = dict()
    for fdef in c.body:
        if not isinstance(fdef, ast.FunctionDef): continue
        selfattributes[fdef] = MembersUsedInMethod().visit(fdef)
    for fdef in selfattributes:
        usedhere = selfattributes[fdef]
        for a in usedhere:
            a_used_elsewhere = False
            for fdefprime in selfattributes:
                if fdefprime == fdef: continue
                if a == fdefprime.name: a_used_elsewhere = True
                if a in selfattributes[fdefprime]: a_used_elsewhere = True
            if not(a_used_elsewhere):
                selfname = fdef.args.args[0].arg
                fdefnew = utils.AttributeNodeReplacer([selfname, a], f"self_{a}").visit(fdef)
                fdef.body = fdefnew.body
    ast.fix_missing_locations(c)
