# Inlining

## Calling conventions

Input: When a function or class is an input, it can usually be given either as a function directly, a string containing the source code of the function, or an `ast.FunctionDef` node.

Output: When a function or class is an output, it will be given as a string.

## List of functions


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
