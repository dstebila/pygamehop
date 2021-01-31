def function1(a: int, b: int) -> int:
 c = a + 9
 d = b + 7
 e = c + d
 return e
    
def function2(w: int, b: int) -> int:
    d = b + 7
    u = w + 9
    return u + d

import Verification

f1 = Verification.canonicalize(function1)
print(f1)

f2 = Verification.canonicalize(function2)
print(f2)

print(f1 == f2)
