from __future__ import annotations
# The above is used to allow references to a class within a class definition, so
# that we can return an instance of a class, eg. from a constructor

from typing import List, Optional
import ast
import re

from . import bits
from . import scope


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

defaultPurity = {
    '__regexp__': {  #  Match by regular expression (including for normal functions).  First match used.
        '.*': [1] * 20   # default for functions not otherwise mentioned.  This needs to be LAST
    }
    # example
    # 'MyType': { 'myMethod', [1,0,0,0]}  # self is modified, other arguments are not.
}








##    ##  #######  ########  ######## ######## ########     ###    ##     ## ######## ########   ######  ######## ########
###   ## ##     ## ##     ## ##          ##    ##     ##   ## ##   ##     ## ##       ##     ## ##    ## ##       ##     ##
####  ## ##     ## ##     ## ##          ##    ##     ##  ##   ##  ##     ## ##       ##     ## ##       ##       ##     ##
## ## ## ##     ## ##     ## ######      ##    ########  ##     ## ##     ## ######   ########   ######  ######   ########
##  #### ##     ## ##     ## ##          ##    ##   ##   #########  ##   ##  ##       ##   ##         ## ##       ##   ##
##   ### ##     ## ##     ## ##          ##    ##    ##  ##     ##   ## ##   ##       ##    ##  ##    ## ##       ##    ##
##    ##  #######  ########  ########    ##    ##     ## ##     ##    ###    ######## ##     ##  ######  ######## ##     ##


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
    - scope is only updated when relevant nodes are visited.  If you change a node you may want
        to visit it afterwards to get the scope correct.  To avoid making further changes when 
        doing so, possibly use an attribute self.readonly or similar to signal when visiting should
        not change anything (but you have to check this yourself!)
    - Assign, Name and Attribute nodes have their scopes fixed up after first calling any subclass
        visitors, so if you only change these nodes, but don't add any new nodes, then there is 
        no need to visit them again to fix up the scope.

    TODO:

    - Get this functionality into the NodeVisitor somehow.  Nothing here changes any
     nodes, so it shouldn't be too bad.
     """
    def __init__(self, counter=0, var_format = '_var_{:d}', type_method_purity = None ):
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

        self.type_method_purity = type_method_purity if type_method_purity else defaultPurity

        # start off with a gloabal scope
        self.scopes: List[scope.Scope] = [ scope.Scope(self.type_method_purity) ]

        # Block level scopes are used to keep track of variables that are stored/loaded within a
        # block of code, eg. if body
        # Currently this only keeps track of variable stores
        self.block_scopes: List[scope.Scope] = [ scope.Scope(self.type_method_purity) ]

        # Statement level scopes are used to keep track of variables that are stored/loaded within
        # a single statement and its children
        self.stmt_scopes: List[scope.Scope] = [ scope.Scope(self.type_method_purity) ]

        # Keep track of the parent of the node being transformed
        self.ancestors: List[ast.ast] = list()



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


  #####
 #     #  ####   ####  #####  ######  ####
 #       #    # #    # #    # #      #
  #####  #      #    # #    # #####   ####
       # #      #    # #####  #           #
 #     # #    # #    # #      #      #    #
  #####   ####   ####  #      ######  ####


    # scopes

    def new_scope(self) -> None:
        self.scopes.append(scope.Scope(self.type_method_purity))

    def pop_scope(self) -> scope.Scope:
        return self.scopes.pop()

    def local_scope(self):
        return self.scopes[-1]

    def local_stmt_scope(self):
        return self.stmt_scopes[-1]

    def new_block_scope(self) -> None:
        self.block_scopes.append(scope.Scope(self.type_method_purity))

    def pop_block_scope(self) -> scope.Scope:
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

    def var_value(self, varname: str) -> Optional[ast.AST]:
        ''' Gives the most recent value assigned to varname.  If the value connot
        be determined (eg. a function argument, or if the varname was assigned
        in the body/orelse of an if statement) then a scope.NoValue object is returned.
        '''
        for s in self.scopes[::-1]:
            if s.in_scope(varname): return s.var_value(varname)
        return None

    def var_value_assigner(self, varname: str) -> Optional[ast.stmt]:
        '''Gives the most recent statement which assigned to varname, or None if
        not found.
        '''
        for s in reversed(self.scopes):
            a = s.var_assigner(varname)
            if a: return a

        return None

    def add_method_call(self, varname: str, caller: ast.stmt) -> None:
        for s in reversed(self.scopes):
            if s.in_scope(varname):
                s.add_method_call(varname, caller)

        for s in reversed(self.block_scopes):
           if s.in_scope(varname):
                s.add_method_call(varname, caller)

        # For statement we don't want to search up the stack of scopes since
        # these will not capture all variable assigns
        self.local_stmt_scope().add_method_call(varname, caller)


    def add_var_load(self, varname, load_type = None):
        ''' Add the variable name to the current scope as a load.  If it is not
        in scope, then continue adding the outer scopes until either the
        variable is found in a scope, or we reach the outermost scope.
        '''
        for s in reversed(self.scopes):
            if s.add_var_load(varname, load_type):
                break
        for s in reversed(self.block_scopes):
            if s.add_var_load(varname, load_type):
                break

        # For statement we don't want to search up the stack of scopes since
        # these will not capture all variable assigns
        self.local_stmt_scope().add_var_load(varname, load_type)

    def add_var_store(self, varname: str, stmt: ast.stmt) -> None:
        ''' Record a ast.Store event on a Name or Attribute.  This is called instead of add_var_assignment
        when the value is not known, for example when varname is an argument to a function/method that might change
        the value.
        '''
        self.local_scope().add_var_store(varname, stmt)
        self.block_scopes[-1].add_var_store(varname, stmt)
        self.stmt_scopes[-1].add_var_store(varname, stmt)        

    def add_var_assignment(self, varname: str, stmt: ast.stmt, value: Optional[ast.expr]) -> None:
        ''' Add a variable name to scope, storing the associated value expression
        '''
        self.local_scope().add_var_assignment(varname, stmt, value)
        self.block_scopes[-1].add_var_assignment(varname, stmt, value)
        self.stmt_scopes[-1].add_var_assignment(varname, stmt, value)


    def add_attribute_store_to_scope(self, attribute:ast.Attribute, stmt: ast.stmt, value: Optional[ast.expr]):
            varname = bits.fqn_str(bits.attribute_fqn(attribute))
            self.add_var_assignment(varname, stmt, value)

    def add_target_to_scope(self, target, s: ast.stmt, value: Optional[ast.expr]):
        ''' Process an assign's target (which could be a tuple), figuring out
        the appropriate value from the given assign value'''

        # assign to object attribute, eg. blah.thing, handling multiple levels like blah.thing.gadget
        if isinstance(target, ast.Attribute):
            self.add_attribute_store_to_scope(target, s, value)

        # assign to a single variable
        elif isinstance(target, ast.Name):
            self.add_var_assignment(target.id, s, value)

        # assign to a tuple
        elif isinstance(target, ast.Tuple):
            # if value is also a tuple then we can match target[j] with value[j]
            if isinstance(value, ast.Tuple):
                if not len(value.elts) == len(target.elts):
                    raise ValueError("Attempt to assign to a tuple from another tuple of different length")
                for i, v in enumerate(value.elts):
                    assigned_node = target.elts[i]
                    if isinstance(assigned_node, ast.Name):
                        self.add_var_assignment(assigned_node.id, s, v)
                    elif isinstance(assigned_node, ast.Attribute):
                        self.add_attribute_store_to_scope(assigned_node, s, v)
                    else:
                        # Don't know how to assign to things that aren't names or attributes.
                        assert(False)
            else:
                for t in target.elts:
                    if isinstance(t, ast.Name):
                        self.add_var_assignment(t.id, s, None)
                    elif isinstance(t, ast.Attribute):
                        self.add_attribute_store_to_scope(t, s, None)
                    else:
                        # Don't know how to assign to things that aren't names or attributes.
                        assert(False)

    def vars_in_scope(self) -> List[str]:
        ''' Returns a list of all variables and parameters currently in scope, including outer
        scopes.'''
        return sum(( s.names_in_scope() for s in self.scopes ), [])

    def vars_in_local_scope(self) -> List[str]:
        ''' Returns a list of variables and parameters in the current local scope only.'''
        return self.local_scope().names_in_scope()

    def method_purity(self, methodName: str) -> List[int]:
        # This is an object method.  Search the scopes for the object to get the purity            
        for s in self.scopes[::-1]:
            if s.in_scope(methodName):
                ret = s.method_purity(methodName)
                if ret: return ret
                break

        # Look for matches by regular expression
        for exp, purity in self.type_method_purity['__regexp__'].items():
            if re.match(exp, methodName):
                return purity

        # If we get here then something messed up or there was no sensible default regexp.
        assert(False)


 ######
 #     #   ##   #####  ###### #    # #####  ####
 #     #  #  #  #    # #      ##   #   #   #
 ######  #    # #    # #####  # #  #   #    ####
 #       ###### #####  #      #  # #   #        #
 #       #    # #   #  #      #   ##   #   #    #
 #       #    # #    # ###### #    #   #    ####


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



 #     #
 #     # #  ####  # #####  ####  #####   ####
 #     # # #      #   #   #    # #    # #
 #     # #  ####  #   #   #    # #    #  ####
  #   #  #      # #   #   #    # #####       #
   # #   # #    # #   #   #    # #   #  #    #
    #    #  ####  #   #    ####  #    #  ####




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

        # If a variable was assigned in either branch, or both, then we assign scope.NoValue() since
        # the value may depend on the test, or may not have been assigned.
        # If a variable was already in scope, update to have scope.NoValue() since we don't
        # know what the value will be
        vars_in_scopes = ifscope.names_in_scope() + elsescope.names_in_scope()  # all variables assigned in the bodies, with multiplicity
        vars_to_store = bits.unique_elements(vars_in_scopes)
        for v in vars_to_store:
            bodyvalue = ifscope.var_value(v)
            orelsevalue = elsescope.var_value(v)

            # If body and else agree on a value, then we can assign it.
            if bodyvalue is not None and orelsevalue is not None and ast.unparse(bodyvalue) == ast.unparse(orelsevalue):
                value = bodyvalue
            else:
                value = None

            self.add_var_assignment(v, node, value)

        # all done fixing the scopes

        # TODO: What about variable loads?  We got rid of them by reverting to old_scope
        self.pop_parent()
        return node

    def visit_While_test(self, t):
        return self.visit(t)

    def visit_While_body(self, body):
        return self.visit_stmts(body)
   
    def visit_While_orelse(self, body):
        return self.visit_stmts(body)

    def visit_While(self, node):
        self.push_parent(node)

        # Whiles need special attention when dealing with scopes because a variable may be assigned to
        # in the body or the orelse.  Also, we can't really know what the values of any variables are
        # because they can change on each iteration of the loop, and we won't know if a break
        # causes the orelse to be skipped

        # no problem with scopes for the test!
        node.test = self.visit_While_test(node.test)

        # We need to be careful whith values, sicne the body may overwrite some variables, and the stored 
        # values in scope will not be correct for subsequent iterations.  Here we just report scope.NoValue
        # for everything in scope while processing the body, which is overly conservative but probably safer.
        # TODO: can we be less conservative?
        self.local_scope().report_values = False
        self.local_scope().store_values = False

        # create a new block level scope for the body to keep track of its loads and stores
        self.new_block_scope()
        node.body = self.visit_While_body(node.body)
        bodyscope = self.pop_block_scope()

        self.local_scope().report_values = True
        self.local_scope().store_values = True

        # For variables stored by the body, we can't be sure about what the value is since
        # in can change every iteration, or there can be no iterations. Overwrite those 
        # stores with scope.NoValue and the While node as the assigner.
        for v in bodyscope.vars_in_scope():
            self.add_var_assignment(v, node, None)

        # create a new block level scope for the orelse to keep track of its loads and stores
        self.new_block_scope()
        node.orelse = self.visit_While_orelse(node.orelse)
        elsescope = self.pop_block_scope()

        # If the else body stored a variable, then we add a new store with scope.NoValue as the value
        # and the While node as the assigner indicating that the While statement may have stored 
        # the variable but we can't be sure what its value is
        for v in elsescope.vars_in_scope():
            self.add_var_assignment(v, node, None)

        # all done fixing the scopes

        self.pop_parent()
        return node



 ###
  #  #    # ##### ###### #####  #    #   ##   #         #    # #  ####  # #####  ####  #####   ####
  #  ##   #   #   #      #    # ##   #  #  #  #         #    # # #      #   #   #    # #    # #
  #  # #  #   #   #####  #    # # #  # #    # #         #    # #  ####  #   #   #    # #    #  ####
  #  #  # #   #   #      #####  #  # # ###### #         #    # #      # #   #   #    # #####       #
  #  #   ##   #   #      #   #  #   ## #    # #          #  #  # #    # #   #   #    # #   #  #    #
 ### #    #   #   ###### #    # #    # #    # ######      ##   #  ####  #   #    ####  #    #  ####


    def _visit_Name(self, node):
        node = self.call_subclass_visitor(node)

        # this might have changed to a different type of node
        if not isinstance(node, ast.Name): return node

        if isinstance(node.ctx, ast.Load):
            # if this is in an ast.Attribute, then this value isn't being loaded, but an attribute of it is.
            # Don't load this Name.  It will be handled by the parent, which is the attribute of this Name.
            if isinstance(self.parent(), ast.Attribute):
                return node

            self.add_var_load(node.id, self.parent_statement())         

        return node

    def _visit_Attribute(self, node):
        node = self.call_subclass_visitor(node)

        # We need to add variable node for all objects in an attribute, eg. for a.b.c
        # we add loads for a, a.b, and a.b.c.  Note that since this function
        # will be called for every Attribute node, we only need to record one load
        # for the object/attr represented by this Attribute node.  Inner object/attrs
        # will be handled by other calls to _visit_Attribute
        if isinstance(node, ast.Attribute):
            # _visit_Name or _visit_Arg will handle the innermost load.  TODO: if the innermost object is an arg, do we want to add these as arg load, or variable load?
            if not isinstance(node.ctx, ast.Load):
                # Stores are handled by _visit_Assign() 
                return node

            # if this is a method call, like a.blarg()
            if isinstance(self.parent(), ast.Call) and node is self.parent().func:
                self.local_scope().add_method_call(bits.fqn_str(bits.attribute_fqn(node)), self.parent_statement()) 
                return node

            # if this is in an ast.Attribute, then this value isn't being loaded, but an attribute of it is.
            # Don't record this load.  It will be handled by the parent (which is actually an attribute of this attribute)
            if isinstance(self.parent(), ast.Attribute):
                return node

            varname = ".".join(bits.attribute_fqn(node))
            self.add_var_load(varname, self.parent_statement())

        return node

    def _visit_Assign(self, node):
        # if there are many targets (eg. a = b = 1) we handle each one

        node = self.call_subclass_visitor(node)

        # this might not be an Assign after above call.
        if isinstance(node, ast.Assign):
            for v in node.targets:
                self.add_target_to_scope(v, node, node.value)

        return node

    def _visit_FunctionDef(self, node):
        # Functions create a new scope
        self.new_scope()

        # Function parameters will be in scope
        # TODO this is probelematic: we need parameters to be in scope so that
        # they are set up when visiting the body (as part of call_subclass_visitor below)
        # but if the node is changed to something other than a FunctionDef then those
        # parameters should not be in scope any more.
        for arg in node.args.args:
            self.local_scope().add_parameter(arg.arg, arg.annotation)


        node = self.call_subclass_visitor(node)

        # TODO: figure out the purity of the function def automatically?

        # We must pop the scope before adding the functionDef to scope, because the current
        # scope is for the body of the function.  The functionDef must be added to the scope
        # in which it sits
        self.pop_scope()

        # make sure this is still a FunctionDef, since the subclass may have changed it
        if isinstance(node, ast.FunctionDef):
            # Add this as a name to the scope
            self.add_var_assignment(node.name, node, node)

        return node

    def _visit_Call(self, node):
        node = self.call_subclass_visitor(node)
        if not isinstance(node, ast.Call):
            return node

        functionName = bits.called_function_name(node)
        self.add_var_load(functionName)

        # Record change to arguments for non-pure functions
        purity = self.method_purity(functionName)
        print(purity)
        for argindex, arg in enumerate(node.args):
            if isinstance(node.func, ast.Attribute) and argindex == 0:
                # This is the object whose method has been called.  This will be handled by the objectvalue in the scope.
                continue
            print(argindex)
            if purity[argindex] == 1:
                # this call may have modified this argument, so add a store
                if isinstance(arg, ast.Name):
                    self.add_var_store(arg.id, self.parent_statement())
                if isinstance(arg, ast.Attribute):
                    fqn = bits.fqn_str(bits.attribute_fqn(arg))
                    self.add_var_store(fqn, self.parent_statement())
        return node

    def _visit_ClassDef(self, node):
        # Classes create a new scope
        self.new_scope()
        node = self.call_subclass_visitor(node)
        self.pop_scope()
        return node



 ###
  #  #    # ###### #####    ##    ####  ##### #####  #    #  ####  ##### #    # #####  ######
  #  ##   # #      #    #  #  #  #        #   #    # #    # #    #   #   #    # #    # #
  #  # #  # #####  #    # #    #  ####    #   #    # #    # #        #   #    # #    # #####
  #  #  # # #      #####  ######      #   #   #####  #    # #        #   #    # #####  #
  #  #   ## #      #   #  #    # #    #   #   #   #  #    # #    #   #   #    # #   #  #
 ### #    # #      #    # #    #  ####    #   #    #  ####   ####    #    ####  #    # ######


    def visit_stmt(self, stmt: ast.stmt):
        # First, visit with any more specific visit function
        visit_val = self.visit_internal(stmt)

        if len(self.prelude_statements[-1]) == 0:
            return visit_val

        # all statements are eligible to have preludes in front of them
        ret_val = self.pop_prelude_statements() + bits.ensure_list(visit_val)

        return ret_val

    def visit_expr(self, expr: ast.expr):
        return self.visit_internal(expr)

    # list visitors

    def visit_stmts(self, stmts: List[ast.stmt]) -> List[ast.AST]:
        # push a new context for prelude statements so that we only
        # process preludes from this block of statements
        self.prelude_statements.append(list())
        ret_val = bits.glue_list_and_vals([ self.visit(stmt) for stmt in stmts])

        # we should have processed all preludes by now.  End of block
        # so pop off the current prelude context
        assert(len(self.prelude_statements[-1]) == 0)
        self.prelude_statements.pop()
        return ret_val

    def visit_exprs(self, exprs: List[ast.expr]) -> List[ast.AST]:
        return bits.glue_list_and_vals([ self.visit(expr) for expr in exprs ])

    def visit_child_list(self, children: List) -> List:
        return bits.glue_list_and_vals([ self.visit(v) for v in children ])

    def visit_statements(self, stmts: List[ast.stmt]) -> List[ast.stmt]:
        # overwrite the old statements with whatever we get back
        stmts[:] = sum( [ bits.ensure_list(self.visit(stmt)) for stmt in stmts ] , [])
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
            self.stmt_scopes.append(scope.Scope(self.type_method_purity))
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
