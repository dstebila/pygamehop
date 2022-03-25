import ast

import gamehop.utils

class Textify(ast.NodeVisitor):

    def visit_ClassDef(self, cdef):
        s = "Class " + cdef.name
        s += "\n" + ''.join(["=" for i in range(len(s))]) + "\n"
        for node in cdef.body:
            if isinstance(node, ast.FunctionDef):
                s += "\n" + self.visit_FunctionDef(node)
            else: raise ValueError(f"Unknown node type {ast.unparse(node)}")
        return s

    def visit_FunctionDef(self, fdef):
        s = ""
        if fdef.name.startswith("o_"): s += "Oracle " + fdef.name
        elif fdef.name == "__init__": return ""
        else: s += fdef.name
        s += "("
        s += ', '.join([arg.arg for arg in fdef.args.args[1:]])
        s += "):"
        s += "\n" + ''.join(["-" for i in range(len(s))]) + "\n"
        for node in fdef.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    s += str(self.visit(target)) + " <- "
                s += str(self.visit(node.value))
                s += "\n"
            elif isinstance(node, ast.Return):
                s += "return " + str(self.visit(node.value)) + "\n"
            elif isinstance(node, ast.If):
                s += "unsupported if statement\n"
            else: raise ValueError(f"Unknown node type {ast.unparse(node)}")
        return s

    def visit_Attribute(self, node):
        base = self.visit(node.value)
        if base == 'self': return node.attr
        else: return base + "." + node.attr

    def visit_Name(self, node):
        return node.id

    def visit_Constant(self, node):
        return str(node.value)

    def visit_BinOp(self, node):
        return str(self.visit(node.left)) + " " + self.visit(node.op) + " " + str(self.visit(node.right))
    def visit_Add(self, node): return "+"

    def visit_Call(self, node):
        s = str(self.visit(node.func))
        s += "("
        s += ', '.join([str(self.visit(arg)) for arg in node.args])
        s += ")"
        return s

    def visit_Tuple(self, node):
        s = "("
        s += ', '.join([str(self.visit(elt)) for elt in node.elts])
        s += ")"
        return s

def textify(cdef: ast.ClassDef) -> str:
    return Textify().visit(gamehop.utils.get_class_def(cdef))
