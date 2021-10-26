from __future__ import annotations
from typing import Optional, List, Union, Dict
import ast
from . import bits

class NoValue():
    '''Used in Scope() objects to indicate that a variable has no value assigned'''

class ObjectValue():
    '''Used it Scope() objects to store the value for an object associated with a variable.
    ObjectValue stores a dictionary of ObjectValues corresponding to its attributes'''
    def __init__(self, assigner: Optional[ast.stmt], value: Optional[ast.expr] = None):
        self.attributes: Dict[str, ObjectValue] = dict()        # Attribute name to ObjectValue maps.  These are attributes of this object.
        self.assigner: Optional[ast.stmt] = assigner            # Statement that created this object in the first place.
        self.method_callers: List[ast.stmt] = list()            # Statements that called methods on this object directly, which may have changed it.  TODO: some way to handle methods that only read?
        self.loaders: List[ast.stmt] = list()                   # Statements that have loaded this object directly
        self.value: Optional[ast.expr] = None                   # The expression originally assigned to this object.
        self.annotation = None                                  # Type annotation for this object

    def modifier_stmts(self) -> List[ast.stmt]:
        ''' Returns a list of statements that have modified this object.  This includes 
        the original assigner statement, any statements that call methods on this object,
        and any modifier statements for attributes of this object.'''
        if self.assigner is not None:
            ret = [ self.assigner ]
        else:
            ret = list()
        ret.extend(self.method_callers)
        for attr in self.attributes.values():
            ret.extend(attr.modifier_stmts())
        return ret

    def loader_stmts(self) -> List[ast.stmt]:
        ''' Returns a list of statements that have loaded this object or any of its attributes.'''
        ret = list(self.loaders)
        for attr in self.attributes.values():
            ret.extend(attr.loader_stmts())
        return ret

    def add_load(self, fqn: List[str], stmt: ast.stmt) -> None:
        self.loaders.append(stmt)

        # If this is a load of an attribute, we need to keep track of that in the attribute.
        if len(fqn) > 0:
            attr = fqn[0]

            # If the attribute has not been explicitly set, it might still exist on the object.
            # Here we create an attribute to keep track of the fact that it was loaded.
            if attr not in self.attributes:
                self.attributes[attr] = ObjectValue(None, None)

            self.attributes[attr].add_load(fqn[1:], stmt)

    def add_attribute_assignment(self, fqn: List[str], assigner: ast.stmt, value: Optional[ast.expr]) -> None:
        # The value currently stored for this object is no longer valid since one of its attributes has changed
        self.value = None

        attr = fqn[0]
       # If this is in an attribute of an attribute, then recurse.
        if len(fqn) > 1:
            # If the attribute has not been explicitly set, it might still exist on the object.
            # Here we create an attribute to keep track of the fact that it was loaded.
            if attr not in self.attributes: 
                self.attributes[attr] = ObjectValue(None, None)
            self.attributes[attr].add_attribute_assignment(fqn[1:], assigner, value)
        else:
            self.attributes[attr] = ObjectValue(assigner, value)
           
    def add_method_call(self, fqn: List[str], stmt: ast.stmt) -> None:
        self.method_callers.append(stmt)

        # If this is a load of an attribute, we need to keep track of that in the attribute.
        if len(fqn) > 0:
            attr = fqn[0]

            # If the attribute has not been explicitly set, it might still exist on the object.
            # Here we create an attribute to keep track of the fact that it was loaded.
            if attr not in self.attributes:
                self.attributes[attr] = ObjectValue(None, None)

            self.attributes[attr].add_method_call(fqn[1:], stmt)
       

class Scope():
    ''' Scope is used by the NodeTraverser to keep track of all variables and function
    parameters currently in scope, plus additional information such as the most
    recently assigned value, and any variables that were referenced that were
    not in this scope at the time.
    '''
    def __init__(self):
        self.parameters = list()                            # function parameters defined in this scope
        self.vars_loaded = list()                           # variables that have been loaded, in order by first load
        self.variables: Dict[str, ObjectValue] = dict()     # Variable names and their currently assigned ObjectValue
        self.external_vars = list()                         # variables loaded that were not previously stored and are not parameters

        self.report_values = True           # In some cases (eg. while loops) we don't want to report the value of variables.
        self.store_values = True            # In some cases we don't want to store values because they may become incorrect later (eg. while loops)

    def add_parameter(self, par_name, annotation = None):
        self.parameters.append(par_name)
        self.variables[par_name] = ObjectValue(None, None)
        self.variables[par_name].annotation = annotation

    def add_assignment(self, fqn: List[str], assigner: ast.stmt, value: Optional[ast.expr])-> None:
        assert(len(fqn) > 0)
        if len(fqn) == 1:
            self.variables[fqn[0]] = ObjectValue(assigner, value)
        else:
            if fqn[0] not in self.variables:
                self.variables[fqn[0]] = ObjectValue(None, None)
            self.variables[fqn[0]].add_attribute_assignment(fqn[1:], assigner, value)

    def add_var_load(self, varname: List[str]):
        ''' Adds the given variable name to the scope, treat as a load.  If this name is
        already known as a parameter or variable in this scope, then records this reference
        and returns True. If the name is not in this scope then returns False
        '''
        pass

    def vars_in_scope(self) -> List[str]:
        pass

    def unique_vars_in_scope(self) -> Optional[List[str]]:
        ''' Returns a list of variables in scope, given in order by most recent store'''
        pass

    def var_value(self, var:str) -> Union[ast.expr, NoValue, None]:
        pass

    def var_assigner(self, var:str, ignore_attribute_assigns = False) -> Optional[ast.stmt]:
        pass

    def var_annotation(self, var:str):
        pass

    def in_scope(self, varname):
        pass

    def names_in_scope(self):
        return self.parameters + self.vars_in_scope()


