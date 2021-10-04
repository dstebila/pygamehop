from __future__ import annotations
# The above is used to allow references to a class within a class definition, so
# that we can return an instance of a class, eg. from a constructor

import ast
from typing import List, Optional, Union, TypeVar, Sequence


T = TypeVar('T')
def ensure_list(thing: Union[T, List[T]]) -> List[T]:
    ''' Argument is wrapped in a list() if it is not already a list'''
    if isinstance(thing, list):
        return thing
    else:
        return [ thing ]

def glue_list_and_vals(vals: List[Union[T, List[T], None]]) -> List[T]:
    ''' Create a single list out of vals.  If a val is a list, then it's
    contents are added to the list, otherwise the val itself is added.
    Any None values are removed.'''
    ret_val: List[T] = list()
    for v in vals:
        if isinstance(v, list):
            ret_val.extend(v)
        elif v is None:
            continue
        else:
            ret_val.append(v)
    return ret_val

def append_if_unique(list, val):
    if not val in list:
        list.append(val)

# type checking is difficult for this one.  mypy doesn't understand that
# we filter on nodetype, which causes problems downstream
def nodes(node, nodetype = ast.AST):
    ''' Generate nodes by depth first traversal of an AST or
    a list of ASTs.  Optionally, filter by node type.'''
    if isinstance(node, list):
        for i in node:
            yield from nodes(i, nodetype)
    else:
        if isinstance(node, nodetype): yield node
        if hasattr(node, '_fields'):
            for field_name in getattr(node, '_fields'):
                if not hasattr(node, field_name): continue
                field = getattr(node, field_name)
                yield from nodes(field, nodetype)

class NoValue():
    '''Used in Scope() objects to indicate that a variable has no value assigned'''

class Scope():
    ''' Scope is used by the NodeTraverser to keep track of all variables and function
    parameters currently in scope, plus additional information such as the most
    recently assigned value, and any variables that were referenced that were
    not in this scope at the time.
    '''
    def __init__(self):
        self.parameters = list()            # function parameters defined in this scope
        self.vars_stored = list()           # variables that have been stored, in order by first store
        self.vars_loaded = list()           # variables that have been loaded, in order by first load
        self.external_vars = list()         # variables loaded that were not previously stored and are not parameters
        self.parameters_loaded = list()     # parameters that have been read by a load, in order by first load
        self.var_values = dict()            # most recent value assigned to variable.  key = variable name, value = assigned value
        self.var_value_assigner = dict()    # most recent statement node to assign to a variable.  key = variable name, value = statement
        self.var_annotations = dict()       # most recent type annotation for a variable

    def add_parameter(self, par_name, annotation = NoValue()):
        self.parameters.append(par_name)
        self.var_values[par_name] = NoValue()    # parameters will not have a value until the function is called
        self.var_annotations[par_name] = annotation

    def add_var_store(self, varname, value, s: ast.stmt, annotation = None):
        append_if_unique(self.vars_stored, varname)
        self.var_values[varname] = value
        self.var_annotations[varname] = annotation
        self.var_value_assigner[varname] = s

    def add_var_load(self, varname):
        ''' Adds the given variable name to the scope, treat as a load.  If this name is
        already known as a parameter or variable in this scope, then records this reference
        and returns True. If the name is not in this scope then returns False
        '''
        # variables stored will always assigned after the start of the function, so if this
        # has happened then a Load refers to the stored variable, not a parameter
        if varname in self.vars_stored:
            append_if_unique(self.vars_loaded, varname)
            return True
        elif varname in self.parameters:
            append_if_unique(self.parameters_loaded, varname)
            return True
        else:
            # the variable is not in scope
            append_if_unique(self.external_vars, varname)
            return False

    def var_value(self, varname):
        return self.var_values[varname]

    def in_scope(self, varname):
        return varname in self.parameters or varname in self.vars_stored

    def names_in_scope(self):
        return self.parameters + self.vars_stored

    def copy(self) -> Scope:
        ret = Scope()
        ret.parameters = self.parameters[:]
        ret.vars_stored = self.vars_stored[:]
        ret.vars_loaded = self.vars_loaded[:]
        ret.external_vars = self.external_vars[:]
        ret.parameters_loaded = self.parameters_loaded[:]
        ret.var_values = dict(self.var_values)
        ret.var_value_assigner = dict(self.var_value_assigner)
        ret.var_annotations = dict(self.var_annotations)
        return ret

    def diff(self, other: Scope) -> Scope:
        '''Return a Scope object whose various lists are those of the
        current object with elements from the other object's lists removed'''
        ret = Scope()
        ret.parameters = [ p for p in self.parameters if p not in other.parameters ]
        ret.vars_stored = [ p for p in self.vars_stored if p not in other.vars_stored ]
        ret.vars_loaded = [ p for p in self.vars_loaded if p not in other.vars_loaded ]
        ret.external_vars = [ p for p in self.external_vars if p not in other.external_vars ]
        ret.parameters_loaded = [ p for p in self.parameters_loaded if p not in other.parameters_loaded ]
        ret.var_values = { k: v for k,v in self.var_values.items() if k not in other.var_values }
        ret.var_value_assigner = { k: v for k,v in self.var_value_assigner.items() if k not in other.var_value_assigner }
        ret.var_annotations = { k: v for k,v in self.var_annotations.items() if k not in other.var_annotations }
        return ret

class NodeTraverser():
    """Improved AST tree traversal over the ast.NodeTransformer class.
    Improved features:
    - the ability to handle List[ast.stmt] using visit_statements()
    - keeping track of variables defined, respecting scopes.  i.e.
        variables defined functionDefs and ClassDefs are removed from the
        scope when those nodes have been processed.  Also, variables defined
        in the body or orelse of if statements are only added to the scope if
        they are defined in _both_ branches.  Locally, each branch keeps track
        of all variables it defines
    - keeping track of the parent of nodes as they are processed, available through
        parent(), which returns None if there is no parent, eg. if this a top-level node
    - if you need a new variable name, unique_variable_name() will give you one.
        each call returns a new name.

    Thinks to keep in mind:
    - if you define any of these functions then you must deal with the scopes etc. yourself
        see the functions below to use as a template:
        - visit_If
    - if you define __init__ then you must call super().__init__() to get
        the local variables set up correctly

    TODO:
    - What to do about scopes when a node changes?  Currently we only look at stores
        at level of the node(s), not recursively.

    - do block level scopes in addition to normal scopes.  This would allow things like
        nicer handling of the scopes for if body/orelse rather than messing with the real
        scopes.  Also, would make it easy to figure out what variables a block depends on
        and assigns to, which is probably required to handle reordering statements in bodies.

    - Get this functionality into the NodeVisitor somehow.  Nothing here changes any
     nodes, so it shouldn't be too bad.
     """
    def __init__(self, counter=0, var_format = '_var_{:d}'):
        ''' counter sets the starting value for unique_variable_name() calls.
        var_format gives the string format for unique_variable_name() calls.
        '''
        # TODO: does this belong here? or should it be in a separate class?
        # State for unique_variable_name() calls
        self.unique_string_counter: int = counter
        self.var_format = var_format

        # prelude_statements are kept track of as a stack so that
        # a statement with a body (eg. If) has separate prelude statements
        # for before it than within its body
        self.prelude_statements: List[List[ast.stmt]] = [list()]

        # start off with a gloabal scope
        self.scopes = [ Scope() ]

        # Block level scopes are used to keep track of variables that are stored/loaded within a
        # block of code, eg. if body
        # Currently this only keeps track of variable stores
        self.block_scopes = [ Scope() ]

        # Statement level scopes are used to keep track of variables that are stored/loaded within
        # a single statement and its children
        self.stmt_scopes = [ Scope() ]

        # Keep track of the parent of the node being transformed
        self.ancestors = list()

    def unique_variable_name(self):
        ''' returns a new string each time.  This works by using a counter
        that is incremented on each call.  The starting counter value
        and format of string can be set in __init__()
        TODO: do we want a set of formats with a separate counter for each?
        this would make it possible/easy to have more specific formats,
        eg. one for return values, one for if tests, etc.
        '''
        v = self.var_format.format(self.unique_string_counter)
        self.unique_string_counter += 1
        return v

    # Prelude statements

    def add_prelude_statement(self, statement: ast.stmt) -> None:
        self.prelude_statements[-1].append(statement)

    def pop_prelude_statements(self) -> List[ast.stmt]:
        new_statements = self.prelude_statements[-1][:]
        self.prelude_statements[-1] = list()
        return new_statements


    # scopes

    def new_scope(self) -> None:
        self.scopes.append(Scope())

    def pop_scope(self) -> Scope:
        return self.scopes.pop()

    def local_scope(self):
        return self.scopes[-1]

    def local_stmt_scope(self):
        return self.stmt_scopes[-1]

    def new_block_scope(self) -> None:
        self.block_scopes.append(Scope())

    def pop_block_scope(self) -> Scope:
        return self.block_scopes.pop()

    def in_scope(self, varname: str) -> bool:
        ''' Returns True if the given varname is defined in any scope, including
        outer scopes.
        '''
        return any(s.in_scope(varname) for s in self.scopes)

    def in_local_scope(self, varname: str) -> bool:
        ''' Returns True if the given varname is defined in the current local scope.
        Outer scopes are ignored.
        '''
        return self.local_scope().in_scope(varname)

    def var_value(self, varname: str) -> Union[ast.expr, NoValue]:
        ''' Gives the most recent value assigned to varname.  If the value connot
        be determined (eg. a function argument, or if the varname was assigned
        in the body/orelse of an if statement) then a NoValue object is returned.
        '''
        for s in self.scopes[::-1]:
            if s.in_scope(varname): return s.var_value(varname)
        return NoValue()

    def add_var_load(self, varname):
        ''' Add the variable name to the current scope as a load.  If it is not
        in scope, then continue adding the outer scopes until either the
        variable is found in a scope, or we reach the outermost scope.
        '''
        for s in reversed(self.scopes):
            if s.add_var_load(varname):
                break
        for s in reversed(self.block_scopes):
            if s.add_var_load(varname):
                break

        # For statement we don't want to search up the stack of scopes since
        # these will not capture all variable assigns
        self.local_stmt_scope().add_var_load(varname)

    def add_var_store(self, varname: str, value: Union[ast.expr, NoValue], s: ast.stmt) -> None:
        ''' Add a variable name to scope, storing the associated value expression
        '''
        self.local_scope().add_var_store(varname, value, s)
        self.block_scopes[-1].add_var_store(varname, value, s)
        self.stmt_scopes[-1].add_var_store(varname, value, s)


    def add_target_to_scope(self, target, value: ast.expr, s: ast.stmt):
        ''' Process an assign's target (which could be a tuple), figuring out
        the appropriate value from the given assign value'''

        # assign to a single variable
        if isinstance(target, ast.Name,):
            self.add_var_store(target.id, value, s)

        # assign to a tuple
        if isinstance(target, ast.Tuple):
            # if value is also a tuple then we can match target[j] with value[j]
            if isinstance(value, ast.Tuple):
                if not len(value.elts) == len(target.elts):
                    raise ValueError("Attempt to assign to a tuple from another tuple of different length")
                for i, v in enumerate(value.elts):
                    var_Name = target.elts[i]
                    assert(isinstance(var_Name, ast.Name))
                    self.add_var_store(var_Name.id, v, s)
            else:
                for t in target.elts:
                    # We can't pull apart a non-tuple (eg. function call), so we can't determine the value
                    assert(isinstance(t, ast.Name))
                    self.add_var_store(t.id, NoValue(), s)


    def add_var_to_scope_from_nodes(self, nodes: Union[ast.AST, Sequence[ast.AST]]) -> None:
        '''Look at the given node(s), and if they assign to any names, put them in scope.
        This does not work recursively!  It only looks at the top level.  This is correct because
        we only want to add vars that are assigned in this scope, not any inner scopes. Note
        that this is not correct for variable loads or out of scope variables.
        TODO: What about object attributes?
        '''
        if isinstance(nodes, ast.AST):
            nodes = [ nodes ]
        for s in nodes:
            if isinstance(s, ast.Assign):
                # if there are many targets (eg. a = b = 1) we handle each one
                for v in s.targets:
                    self.add_target_to_scope(v, s.value, s)

    def vars_in_scope(self) -> List[str]:
        ''' Returns a list of all variables and parameters currently in scope, including outer
        scopes.'''
        return sum(( s.names_in_scope() for s in self.scopes ), [])

    def vars_in_local_scope(self) -> List[str]:
        ''' Returns a list of variables and parameters in the current local scope only.'''
        return self.local_scope().names_in_scope()


    # Keep track of parent of each node
    def parent(self):
        ''' Returns the node of which the currently visited node is a child.
        Returns None if there is no parent (eg. top level statement).'''
        if len(self.ancestors) < 1:
            return None
        return self.ancestors[-1]

    def parent_statement(self) -> Optional[ast.stmt]:
        ''' Returns the most recent ancestor which is a statement.  If no such ancestor
        exists then returns None'''
        for a in reversed(self.ancestors):
            if isinstance(a, ast.stmt):
                return a

        return None

    def push_parent(self, node):
        self.ancestors.append(node)

    def pop_parent(self):
        self.ancestors.pop()

    # visitor functions

    # These are here so that we can easily override them to hook into If visiting without
    # having to reproduce all the scope stuff
    def visit_If_test(self, test):
        return self.visit(test)

    def visit_If_body(self, body):
        return self.visit_stmts(body)

    def visit_If_orelse(self, body):
        return self.visit_stmts(body)

    def visit_If(self, node):
        self.push_parent(node)

        # ifs need special attention when dealing with scopes because a variable may be assigned to
        # in one branch but not the other, or the values may be different in different branches.

        # no problem with scopes for the test!
        node.test = self.visit_If_test(node.test)

        # remember variables and values currently in the local scope to help fix things up later
        old_scope = self.local_scope().copy()

        # create a new block level scope for the body to keep track of its loads and stores
        self.new_block_scope()
        node.body = self.visit_If_body(node.body)
        ifscope = self.pop_block_scope()

        # restore the saved scope so that changes in the body are not reflected in the orelse
        # remember to copy, otherwise the orelse will overwrite our saved info
        self.scopes[-1] = old_scope.copy()

        # create a new block level scope for the orelse to keep track of its loads and stores
        self.new_block_scope()
        node.orelse = self.visit_If_orelse(node.orelse)
        elsescope = self.pop_block_scope()

        # restore the saved scope to reset it back to before the bodies
        self.scopes[-1] = old_scope

        # we only want to keep variables that were assigned to
        # in _both_ branches, otherwise they may not be defined.
        # If a variable was already in scope, update to have NoValue() since we don't
        # know what the value will be
        vars_in_scopes = ifscope.names_in_scope() + elsescope.names_in_scope()  # all variables assigned in the bodies, with multiplicity
        for v in vars_in_scopes:
            if vars_in_scopes.count(v) == 2 or self.in_local_scope(v):
                self.add_var_store(v, NoValue(), node)
            #TODO: if both assign same value, then we can add that value rather than NoValue

        # all done fixing the scopes

        self.pop_parent()
        return node

    # Internal visitors

    def _visit_FunctionDef(self, node):
        # Functions create a new scope
        self.new_scope()

        # Function parameters will be in scope
        for arg in node.args.args:
            self.local_scope().add_parameter(arg.arg, arg.annotation)

        node = self.call_subclass_visitor(node)
        self.pop_scope()
        return node

    def _visit_ClassDef(self, node):
        # Classes create a new scope
        self.new_scope()
        node = self.call_subclass_visitor(node)
        self.pop_scope()
        return node

    def _visit_Name(self, node):
        node = self.call_subclass_visitor(node)

        # this might have changed to a different type of node
        if not isinstance(node, ast.Name): return node
        if isinstance(node.ctx, ast.Load):
            self.add_var_load(node.id)
        return node

    # parent class visitors

    def visit_stmt(self, stmt: ast.stmt):
        # First, visit with any more specific visit function
        visit_val = self.visit_internal(stmt)

        # If there are no prelude statements to add here, then just
        # return the value.  But first fix up the scope!
        if len(self.prelude_statements[-1]) == 0:
            if visit_val is not None:
                self.add_var_to_scope_from_nodes(visit_val)
            return visit_val

        # all statements are eligible to have preludes in front of them
        ret_val = self.pop_prelude_statements() + ensure_list(visit_val)

        # update the scope based on the up-to-date statements
        self.add_var_to_scope_from_nodes(ret_val)
        return ret_val

    def visit_expr(self, expr: ast.expr):
        return self.visit_internal(expr)

    # list visitors

    def visit_stmts(self, stmts: List[ast.stmt]) -> List[ast.AST]:
        # push a new context for prelude statements so that we only
        # process preludes from this block of statements
        self.prelude_statements.append(list())
        ret_val = glue_list_and_vals([ self.visit(stmt) for stmt in stmts])

        # we should have processed all preludes by now.  End of block
        # so pop off the current prelude context
        assert(len(self.prelude_statements[-1]) == 0)
        self.prelude_statements.pop()
        return ret_val

    def visit_exprs(self, exprs: List[ast.expr]) -> List[ast.AST]:
        return glue_list_and_vals([ self.visit(expr) for expr in exprs ])

    def visit_child_list(self, children: List) -> List:
        return glue_list_and_vals([ self.visit(v) for v in children ])

    def visit_statements(self, stmts: List[ast.stmt]) -> List[ast.stmt]:
        # overwrite the old statements with whatever we get back
        stmts[:] = sum( [ ensure_list(self.visit(stmt)) for stmt in stmts ] , [])
        return stmts

    # The stack of functions for calling visitors

    def visit(self, node: ast.AST):
        '''Calls visit_NodeType where NodeType is the name of the type of
        the node passed in.  If this function is not present then instead
        generic_visitor() is called.

        Note: before visit_NodeType is called, parent class visitors (visit_stmt,
        visit_expr) may be called, after which the internal function
        _visit_NodeType() may be called.  These functions are internal to
        NodeTraverser to take care of NodeTraverser base class functionality.

        Order functions are called and duties:
        - visit(): dispatch to parent class visitor or visit_subclass_visitor()
            Current parent class visitors are for ast.stmt and ast.expr:
            - visit_stmt(): call visit_internal, prepend preludes, add variables to scope
            - visit_expr(): call visit_internal
        - visit_internal(): dispatch to internal visitor or visit_subclass_visitor()
            Current internal visitors:
            - _visit_FunctionDef():  push/pop function scope, add function parameters to scope, call visit_subclass_visitor()
            - _visit_ClassDef(): push/pop function scope, call visit_subclass_visitor()
            - _visit_Name(): call visit_subclass_visitor(), if load, add variable to scope
        - call_subclass_visitor(): calls visit_NodeType() if it exits, otherwise calls generic_visit()
            - visit_If(): push/pop parent, fix up scope based on the two branches
                - visit_If_test(): call visit() on the test
                - visit_If_body(): call visit_stmts() on the body
                - visit_If_orelse(): call visit_stmts() on the orelse
        - generic_visit(): push/pop parent, call visit_fields()
        - visit_fields(): call visitor for fields in a node, push/pop block scope for statement blocks
            - for lists:
                - visit_stmts(): push/pop prelude list for this block, call visit() on each stmt in the block
                - visit_exprs(): call visit() on each expr in the list
                - visit_child_list(): call visit() on each node in the list
            - for ast.AST's:
                - visit()


        '''
        if isinstance(node, ast.stmt):
            self.stmt_scopes.append(Scope())
            ret = self.visit_stmt(node)
            self.stmt_scopes.pop()
            return ret

        elif isinstance(node, ast.expr):
            return self.visit_expr(node)
        else:
            return self.call_subclass_visitor(node)

    def visit_internal(self, node: ast.AST):
        '''Calls _visit_NodeType where NodeType is the name of the type of
        the node passed in.  If this function is not present then instead
        call_subclass_visitor() is called.
        '''
        visit_function_name = f"_visit_{type(node).__name__}"
        if hasattr(self, visit_function_name):
            visit_function = getattr(self, visit_function_name)
            return visit_function(node)
        else:
            return self.call_subclass_visitor(node)

    def call_subclass_visitor(self, node: ast.AST):
        '''Calls visit_NodeType where NodeType is the name of the type of
        the node passed in.  If this function is not present then instead
        generic_visit() is called.
        '''
        visit_function_name = f"visit_{type(node).__name__}"
        if hasattr(self, visit_function_name):
            visit_function = getattr(self, visit_function_name)
            return visit_function(node)
        else:
            return self.generic_visit(node)

    def generic_visit(self, node):
        ''' Visit all children of a current node.  This will not call any
        visit_NodeType() functions on the current node.
        '''
        # We need to set this node as parent before we visit its childen
        self.push_parent(node)
        visit_val = self.visit_fields(node)  # this call will only visit children
        self.pop_parent()
        return visit_val

    def visit_fields(self, node: ast.AST) -> Optional[ast.AST]:
        ''' Iterate over all childern of the given node, listed in node._fields.
            This means:
            - if a child is a AST node, then visit() it and replace the current node
                 with the return value
            - if a child is a list of ast.stmt, then visit_stmts() the list and replace the
                 current list with the return value
            - if a child is a list of ast.expr, then visit_exprs() the list and replace the
                 current list with the return value
            - if a child is a list of anything else, then visit_child_list() the list and replace the
                 current list with the return value
            - all other children are not visited
            - empty lists are not visited
        '''
        if node is None: return None
        for field_name in node._fields:
            if hasattr(node, field_name):
                child = getattr(node, field_name)

                if type(child) == list:
                    if len(child) == 0: continue
                    if isinstance(child[0], ast.stmt):
                        self.new_block_scope()
                        child[:] = self.visit_stmts(child)
                        self.pop_block_scope()
                    elif isinstance(child[0], ast.expr):
                        child[:] = self.visit_exprs(child)
                    else:
                        child[:] = self.visit_child_list(child)

                elif isinstance(child, ast.AST):
                    new_child = self.visit(child)
                    if new_child is None:
                        delattr(node, field_name)
                    else:
                        setattr(node, field_name, new_child)
                else:
                    # for now, do nothing, but maybe in the future we will want
                    # to visit non-node fields
                    pass
        return node
