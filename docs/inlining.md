# Inlining

## Calling conventions

Input: When a function or class is an input, it can usually be given either as a function directly, a string containing the source code of the function, or an `ast.FunctionDef` node.

Output: When a function or class is an output, it will be given as a string.

## List of functions

- [Inline argument into function](#inline-argument-into-function)
- [Inline function call](#inline-function-call)
- [Inline calls to all methods of a given class](#inline-calls-to-all-methods-of-a-given-class)
- [Inline all methods of a cryptographic scheme into a cryptographic game](#inline-all-methods-of-a-cryptographic-scheme-into-a-cryptographic-game)
- [Inline reduction into a cryptographic game](#inline-reduction-into-a-cryptographic-game)

### Inline argument into function

Within a function, replaces all uses of an argument with a given value.

```python
def inline_argument_into_function(
	argname: str, 
	val: Union[bool, float, int, str, tuple, list, set, ast.AST], 
	f: Union[Callable, str, ast.FunctionDef]
) -> str:
```

Example:

```python
def f(x, y): print(x)

inline_argument_into_function('x', True, f)

# returns:

def f(y): print(True)
```

Raises:

- `KeyError` if the argument name provided is not actually an argument of the function.
- `ValueError` if the argument is ever assigned to within the function body.

### Inline function call

Within a function replace all calls to another function with their body, with the arguments to the call appropriately bound and with local variables named unambiguously.

```python
def inline_function_call(
	f_to_be_inlined: Union[Callable, str, ast.FunctionDef],
	f_dest: Union[Callable, str, ast.FunctionDef]
) -> str:
```

Example:

```python
def inlinand(a, b):
    c = a + b
	return c
def f(x):
    y = inlinand(x, x)
    z = 2

inline_function_call(inlinand, f)

# returns:

def f(x):
    inlinandᴠ1ⴰc = x + x
    y = inlinandᴠ1ⴰc
    z = 2
```

Raises:

- `NotImplementedError` if the function to be inlined contains a return statement anywhere other than at the end.
- `ValueError` if the destination function calls the function to be inlined in any way other than in a lone assignment statement (i.e., `foo = f(bar)`).
- `ValueError` if the function to be inlined does not have a return statement.

### Inline calls to all methods of a given class

Within a function replace all calls to methods of a class with the body of the method, with the arguments to the call appropriately bound and with local variables named unambiguously.

All methods of the class being inlined must be static methods.

```python
def inline_all_method_calls(
	c_to_be_inlined: Union[Type[Any], str, ast.ClassDef], 
	f_dest: Union[Callable, str, ast.FunctionDef]
) -> str:
```

Example:

```python
class C():
    @staticmethod
    def A(a, b): 
    	r = a + b
    	return r
def f(x): z = C.A(x, 2)

inline_all_method_calls(C, f)

# returns:

def f(x):
    C_Aᴠ1ⴰr = x + 2
    z = C_Aᴠ1ⴰr
```

Raises:

- `ValueError` if the class being inlined has a non-static method.
- `NotImplementedError` and `ValueError` for the reasons given in `inline_function_call`.

### Inline all methods of a cryptographic scheme into a cryptographic game

Within a cryptographic game (a class consisting of multiple methods), replace all calls to methods of a cryptographic scheme (another class consisting of multiple methods) with the body of the corresponding method, with the arguments to the call appropriately bound and with local variables named unambiguously.

All methods of the cryptographic scheme being inlined must be static methods.

```python
def inline_scheme_into_game(
	Scheme: Type[Crypto.Scheme], 
	Game: Type[Crypto.Game]
) -> str:
```

Example:

```python
class P(Crypto.Scheme):
    @staticmethod
    def KeyGen(): return (1, 2)

class G(Crypto.Game):
    def __init__(self, Scheme, Adversary):
        self.Scheme = Scheme
        self.Adversary = Adversary
    def main(self) -> Crypto.Bit:
        adversary = self.Adversary(self.Scheme)
        (pk, sk) = self.Scheme.KeyGen()
        return 0

inline_scheme_into_game(P, G)

# returns:

class G_expected_result(Crypto.Game):
    def __init__(self, Adversary):
        self.Scheme = P
        self.Adversary = Adversary
    def main(self) -> Crypto.Bit:
        adversary = self.Adversary(P)
        (pk, sk) = (1, 2)
        return 0
```

Raises:

- `NotImplementedError` and `ValueError` for the reasons given in `inline_all_method_calls`.

### Inline reduction into a cryptographic game

Suppose R is a reduction showing how transform an adversary for the game GameForR against scheme SchemeForR into adversary for the game TargetGame against scheme TargetScheme.  This procedure generates the result of that inlining process, which is a game with the same interface as TargetGame against scheme TargetScheme.  

The high-level idea of this procedure is as follows:

1. The main method of the result should take the main method of the GameForR and inline all calls to R.
2. R provides methods that will become oracles in the resulting game; these are copied from R.
3. The body of all the oracles of GameForR will be inlined into the resulting game.
4. Various things are renamed and minor things are changed, for example turning static methods into non-static methods.

```python
def inline_reduction_into_game(
	R: Type[Crypto.Reduction], 
	GameForR: Type[Crypto.Game], 
	SchemeForR: Type[Crypto.Scheme], 
	TargetGame: Type[Crypto.Game], 
	TargetScheme: Type[Crypto.Scheme]
) -> str:
```

An example of this is shown in test cases in `tests/gamehop/inlining/test_inline_reduction_into_game.py` (an example without oracles) and `tests/gamehop/inlining/test_inline_reduction_into_game_with_oracles.py` (an example with oracles).

Raises:

- `ValueError` if GameForR is not of the right form.
- `NotImplementedError` and `ValueError` for the reasons given in `inline_scheme_into_game `.
