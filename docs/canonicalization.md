# Canonicalization

To compare two pieces of code and see if they are equivalent, pygamehop first applies a series of transformations that we call "canonicalization", with the aim that two equivalent programs should canonicalize to the same string of source code.

## List of transformations

### If statements to expressions

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
