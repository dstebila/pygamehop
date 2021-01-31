def function1(a: int, b: int) -> int:
 message = "Hello"
 c = a + 9
 d = b + 7
 e = c + d
 return e
    
def function2(w: int, b: int) -> int:
    message = "Hello"
    d = b + 7
    u = w + 9
    return u + d

def addseven(q: int) -> int:
    message = "Hello"
    return q + 7

def function3(w: int, b: int) -> int:
    d = addseven(b)
    u = w + 9
    return u + d

# import ast
# import inspect
# t1 = ast.parse(inspect.getsource(function1))
# print(ast.dump(t1, indent=2))

import Verification
f1 = Verification.canonicalize_function(function1)
print(f1)
f2 = Verification.canonicalize_function(function2)
f3 = Verification.inline_function(function3, addseven)
f3 = Verification.canonicalize_function(f3)
print((f1 == f2) and (f2 == f3))
