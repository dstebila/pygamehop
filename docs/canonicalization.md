# Canonicalization

To compare two pieces of code and see if they are equivalent, pygamehop first applies a series of transformations that we call "canonicalization", with the aim that two equivalent programs should canonicalize to the same string of source code.

## List of transformations

- [If statements to if expression](#if-statements-to-if-expressions)
- [Expand call arguments](#expand-call-arguments)
- [Canonicalize function name](#canonicalize-function-name)
- [Inline lambdas](#inline-lambdas)
- [Collapse assignments](#collapse-assignments)
- [Simplify constant expressions](#simplify-constant-expressions)
- [Canonicalize line order](#canonicalize-line-order)
- [Remove irrelevant statements](#remove-irrelevant-statements)
- [Canonicalize argument order](#canonicalize-argument-order)
- [Canonicalize variable names](#canonicalize-variable-names)

### If statements to if expressions

Converts if statements to if expressions. 

Example:

```python
if condition:
	v = expression1
else:
	v = expression2
	w = expression3

# becomes:

ifcond = condition
v_if = expression1
w_if = None
v_else = expression2
w_else = expression3
v = v_if if ifcond else v_else
w = w_if if ifcond else w_else
```

- Main method: `gamehop.verification.canonicalization.ifstatements.if_statements_to_expressions`

### Expand call arguments

Expands arguments to function calls to be their own statements.

Example:

```python
a = f(g(y))

# becomes:

v = g(y)
a = f(v)
```

- Main method: `gamehop.verification.canonicalization.expand.call_arguments`

### Canonicalize return statement

Simplify the return statement so that it consists of only a constant or a single variable.

Example:

```python
return x + y

# becomes:

z = x + y
return z
```

- Main method: `gamehop.verification.canonicalization.canonicalize_return`

### Canonicalize function name

Rename a function to have a fixed name.

Example:

```python
def myfunc():
    ...

# becomes:

def f():
    ...
```

- Main method: `gamehop.verification.canonicalization.canonicalize_function_name`

### Inline lambdas

Replace all calls to lambda functions with their body.

Example:

```python
adder = lambda b: b + 1
r = adder(c)

# becomes:

r = c + 1
```

- Main method: `gamehop.verification.canonicalization.inline_lambdas`

### Collapse assignments

Simplify chains of assignments where possible.

Example:

```python
a = 7
x = a
b = f(x)

# becomes:

b = f(7)
```

Also works on tuples, such as:

```python
c = (a, b)
(x, y) = x
return x + y

# becomes:

return x + b
```

- Main method: `gamehop.verification.canonicalization.collapse_useless_assigns`

### Simplify constant expressions

Simplify unary, boolean, binary, and compare operators that involve constants.

Example:

```python
a = not(False)
b = True or False
c = 2 + 5
d = (4 != 4)

# becomes:

a = True
b = True
c = 7
d = False
```

Also works on the condition of if expressions, for example:

```python
e = 1 if True else 2

# becomes:

e = 1
```

- Main method: `gamehop.verification.canonicalization.simplify.simplify`

### Canonicalize line order

Reorder lines into a canonical order (while maintaining behaviour).

Example:

```python
c = h(a)
d = g(c)
b = g(c)
return (b, c, d)

# becomes:

c = h(a)
b = g(c)
d = g(c)
return (b, c, d)
```

In the example above, `c = h(a)` obviously must come before either of `b = g(c)` and `d = g(c)`, but the order of the assignments to `b` and `d` can in principle go in any order (assuming `g` is side-effect free, which we always assume). To derive a canonical order, we rely on the order in which the values appear in subsequent statements that use them.

- Main method: `gamehop.verification.canonicalization.canonicalize_line_order`

### Remove irrelevant statements

Remove statements that do not affect the output.

Example:

```python
a = 1
b = 2
return a

# becomes:

a = 1
return a
```

- Main method: This is an effect of `gamehop.verification.canonicalization.canonicalize_line_order`

### Canonicalize argument order

Reorder arguments to a function into a canonical order. Also remove unused arguments.

Example:

```python
def f(x, y, z):
	return y + 2 * x

# becomes:

def f(y, x):
	return y + 2 * x
```

This transformation is relevant when trying to canonicalize functions when treating the functions as a top-level object without regards to their callers, but does not necessarily make sense with inner functions where there are calls to those inner functions in other parts of the code.

- Main method: `gamehop.verification.canonicalization.canonicalize_argument_order`

### Canonicalize variable names

Give consistent names to the variables used in a function.

Example:

```python
def f(x, y):
    a = 7
    return y + a

# becomes:

def f(v0, v1):
    v2 = 7
    return v1 + v2
```

- Main method: `gamehop.verification.canonicalization.canonicalize_variable_names`
