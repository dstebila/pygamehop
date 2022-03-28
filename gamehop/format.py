import ast

import gamehop.utils

def indent_every_line(s: str) -> str:
    lines = s.splitlines()
    newlines = list()
    for line in lines: newlines.append("  " + line)
    return "\n".join(newlines)

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
        s_body = ""
        for node in fdef.body:
            s_body += str(self.visit(node)) + "\n"
        s += indent_every_line(s_body)
        return s

    def visit_Assign(self, node):
        s = ""
        for target in node.targets:
            s += str(self.visit(target)) + " <- "
        s += str(self.visit(node.value))
        return s

    def visit_Attribute(self, node):
        base = self.visit(node.value)
        if base == 'self': return node.attr
        else: return base + "." + node.attr

    def visit_BinOp(self, node):
        return str(self.visit(node.left)) + " " + self.visit(node.op) + " " + str(self.visit(node.right))
    def visit_Add(self, node): return "+"
    def visit_Sub(self, node): return "-"
    def visit_Mult(self, node): return "*"
    def visit_Div(self, node): return "/"
    def visit_FloorDiv(self, node): return "//"
    def visit_Mod(self, node): return "mod"
    def visit_Pow(self, node): return "^"
    def visit_LShift(self, node): return "<<"
    def visit_RShift(self, node): return ">>"
    def visit_BitOr(self, node): return "|"
    def visit_BitXor(self, node): return "xor"
    def visit_BitAnd(self, node): return "&"
    def visit_MatMult(self, node): return "*"

    def visit_BoolOp(self, node):
        op = " " + str(self.visit(node.op)) + " "
        return op.join([str(self.visit(val)) for val in node.values])
    def visit_And(self, node): return "and"
    def visit_Or(self, node): return "or"
    
    def visit_Break(self, node): return "break"

    def visit_Call(self, node):
        s = str(self.visit(node.func))
        s += "("
        s += ', '.join([str(self.visit(arg)) for arg in node.args])
        s += ")"
        return s
    
    def visit_Compare(self, node):
        s = str(self.visit(node.left))
        for i in range(len(node.ops)):
            s += " " + str(self.visit(node.ops[i])) + " " + str(self.visit(node.comparators[i]))
        return s
    def visit_Eq(self, node): return "="
    def visit_NotEq(self, node): return "!="
    def visit_Lt(self, node): return "<"
    def visit_LtE(self, node): return "≤"
    def visit_Gt(self, node): return ">"
    def visit_GtE(self, node): return "≥"
    def visit_Is(self, node): return "is"
    def visit_IsNot(self, node): return "is not"
    def visit_In(self, node): return "in"
    def visit_NotIn(self, node): return "not in"

    def visit_Constant(self, node):
        return str(node.value)

    def visit_Continue(self, node): return "continue"

    def visit_For(self, node):
        s = "for " + str(self.visit(node.target)) + " in " + str(self.visit(node.iter)) + ":\n"
        for line in node.body:
            s += "  " + str(self.visit(line)) + "\n"
        if node.orelse:
            s += "else:\n"
            for line in node.orelse:
                s += "  " + str(self.visit(line)) + "\n"
        return s

    def visit_If(self, node):
        s = "if " + str(self.visit(node.test)) + ":\n"
        for line in node.body:
            s += "  " + str(self.visit(line)) + "\n"
        if node.orelse:
            s += "else:\n"
            for line in node.orelse:
                s += "  " + str(self.visit(line)) + "\n"
        return s

    def visit_IfExp(self, node):
        return str(self.visit(node.body)) + " if " + str(self.visit(node.test)) + " else " + str(self.visit(node.orelse))

    def visit_Name(self, node):
        return node.id

    def visit_Return(self, node):
        return "return " + str(self.visit(node.value))

    def visit_Tuple(self, node):
        s = "("
        s += ', '.join([str(self.visit(elt)) for elt in node.elts])
        s += ")"
        return s

    def visit_UnaryOp(self, node):
        return str(self.visit(node.operand)) + " " + str(self.visit(node.op))

    def visit_AnnAssign(self, node): 
        raise ValueError("Unsupported node type: AnnAssign")
    def visit_Assert(self, node): 
        raise ValueError("Unsupported node type: Assert")
    def visit_AugAssign(self, node): 
        raise ValueError("Unsupported node type: AugAssign")
    def visit_Delete(self, node): 
        raise ValueError("Unsupported node type: Delete")
    def visit_Dict(self, node): 
        raise ValueError("Unsupported node type: Dict")
    def visit_DictComp(self, node): 
        raise ValueError("Unsupported node type: DictComp")
    def visit_Expr(self, node): 
        raise ValueError("Unsupported node type: Expr")
    def visit_GeneratorExp(self, node): 
        raise ValueError("Unsupported node type: GeneratorExp")
    def visit_Global(self, node): 
        raise ValueError("Unsupported node type: Global")
    def visit_Lambda(self, node): 
        raise ValueError("Unsupported node type: Lambda")
    def visit_List(self, node): 
        raise ValueError("Unsupported node type: List")
    def visit_ListComp(self, node): 
        raise ValueError("Unsupported node type: ListComp")
    def visit_Match(self, node): 
        raise ValueError("Unsupported node type: Match")
    def visit_NamedExpr(self, node): 
        raise ValueError("Unsupported node type: NamedExpr")
    def visit_Nonlocal(self, node): 
        raise ValueError("Unsupported node type: Nonlocal")
    def visit_Set(self, node): 
        raise ValueError("Unsupported node type: Set")
    def visit_SetComp(self, node): 
        raise ValueError("Unsupported node type: SetComp")
    def visit_Slice(self, node): 
        raise ValueError("Unsupported node type: Slice")
    def visit_Starred(self, node): 
        raise ValueError("Unsupported node type: Starred")
    def visit_Subscript(self, node): 
        raise ValueError("Unsupported node type: Subscript")
    def visit_Try(self, node): 
        raise ValueError("Unsupported node type: Try")
    def visit_While(self, node): 
        raise ValueError("Unsupported node type: While")
    def visit_With(self, node): 
        raise ValueError("Unsupported node type: With")
    def visit_Yield(self, node):
        raise ValueError("Unsupported node type: Yield")
    def visit_YieldFrom(self, node):
        raise ValueError("Unsupported node type: YieldFrom")

def textify(cdef: ast.ClassDef) -> str:
    return Textify().visit(gamehop.utils.get_class_def(cdef))
