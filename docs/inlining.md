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
