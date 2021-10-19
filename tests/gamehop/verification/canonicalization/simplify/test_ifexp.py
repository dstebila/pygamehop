import ast
import unittest
import gamehop.utils as utils
import gamehop.inlining.internal
import gamehop.verification.canonicalization.simplify as simplify

def f_ifexp(y):
    a = 1 if y else 2
    b = 1 if True else 2
    c = 1 if (3 == 4) else 2
    d = 1 if (3 <= 4) else 2
    e = 1 if (3 != 4) else 2
    f = 1 if (3 > 4) else 2
    g = 1 if (3 > 4) else 2 if (3 > 5) else 3
def f_ifexp_expected_result(y):
    a = 1 if y else 2
    b = 1
    c = 2
    d = 1
    e = 1
    f = 2
    g = 3

def expected_result(f):
    fdef = utils.get_function_def(f)
    fdef.name = fdef.name.replace('_expected_result', '')
    return ast.unparse(fdef)

class TestSimplifyIfExp(unittest.TestCase):
    def test_ifexp(self):
        f = gamehop.utils.get_function_def(f_ifexp)
        f = simplify.simplify(f)
        self.assertEqual(
            ast.unparse(f),
            expected_result(f_ifexp_expected_result)
        )

    def test_if(self):
        def f(y):
            if y:
                z = 1
            else:
                z = 2

            if True:
                a = 1
            else:
                a = 0

            if False:
                b = 0
            else:
                b = 1

            if (3 == 4):
                c = 0
            else:
                c = 1

            if (3 != 4):
                d = 1
            else:
                d = 0

        def f_expected_result(y):
            if y:
                z = 1
            else:
                z = 2

            a = 1
            
            b = 1
            
            c = 1
            
            d = 1

        f_def = gamehop.utils.get_function_def(f)
        f_def = simplify.simplify(f_def)
        self.assertEqual(
            ast.unparse(f_def),
            expected_result(f_expected_result)
        )


