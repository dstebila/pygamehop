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

import Verification

f1 = Verification.canonicalize(function1)
f2 = Verification.canonicalize(function2)
f3 = Verification.inlinefunction(function3, addseven)
f3 = Verification.canonicalize(f3)
assert f1 == f2
assert f2 == f3
