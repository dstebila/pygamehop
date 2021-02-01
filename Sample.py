import Verification

# Some test cases for inlinining and canonicalization

# A basic function
def function1(a: int, b: int) -> int:
 message = "Hello"
 c = a + 9
 d = b + 7
 e = c + d
 return e

# same as function1, but with lines in a different order and returning a result directly rather than a variable
def function2(w: int, b: int) -> int:
    message = "Hello"
    d = b + 7
    u = w + 9
    return u + d

f1 = Verification.canonicalize_function(function1)
f2 = Verification.canonicalize_function(function2)
assert f1 == f2

# same as function1, but with part of it via inlining from another function
def addseven(q: int) -> int:
    message = "Hello"
    return q + 7

def function3(w: int, b: int) -> int:
    d = addseven(b)
    u = w + 9
    return u + d

f3 = Verification.inline_function(function3, addseven)
f3 = Verification.canonicalize_function(f3)
assert f1 == f3

# same as function1, but with part of it via inlining from arguments to the function
class Doer(object):
    def phase1(self, a:int) -> int:
        return a + 9

def function4(a: int, b: int, doer: Doer, seven: int) -> int:
 message = "Hello"
 c = doer.phase1(a)
 d = b + seven
 e = c + d
 return e

f4 = Verification.inline_argument(function4, 'seven', 7)
f4 = Verification.inline_argument(f4, 'doer', Doer)
f4 = Verification.canonicalize_function(f4)
assert f1 == f4

# same as function1, but with some useless assigns
def function5(a: int, b: int) -> int:
 message = "Hello"
 x = a
 c = x + 9
 x = b
 d = x + 7
 e = c + d
 return e

f5 = Verification.canonicalize_function(function5)
assert f1 == f5

print("All tests passed")
