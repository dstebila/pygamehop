from __future__ import annotations
from typing import Optional, List,  Dict
import ast
from . import bits

class NoValue():
    '''Used in Scope() objects to indicate that a variable has no value assigned'''

class ObjectValue():
    '''Used it Scope() objects to store the value for an object associated with a variable.
    ObjectValue stores a dictionary of ObjectValues corresponding to its attributes'''
    def __init__(self, assigner: Optional[ast.stmt], value: Optional[ast.AST] = None):
        self.attributes: Dict[str, ObjectValue] = dict()        # Attribute name to ObjectValue maps.  These are attributes of this object.
        self._assigner: Optional[ast.stmt] = assigner           # Statement that created this object in the first place.
        self.method_callers: List[ast.stmt] = list()            # Statements that called methods on this object directly, which may have changed it.  TODO: some way to handle methods that only read?
        self.attribute_assigners: List[ast.stmt] = list()
        self.loaders: List[ast.stmt] = list()                   # Statements that have loaded this object directly
        self.loaded: bool = False
        self.assigned:bool = False                              # Has this object actually been assigned?  It may have been created as a container to record a load
        self._value: Optional[ast.AST] = value                  # The expression originally assigned to this object.
        self._annotation = None                                 # Type annotation for this object
        if assigner is not None:
            self.assigned = True

    def copy(self) -> ObjectValue:
        ret = ObjectValue(self._assigner, self._value)
        ret.method_callers = list(self.method_callers)
        ret.attribute_assigners = list(self.attribute_assigners)
        ret.loaders = list(self.loaders)
        ret.loaded = self.loaded
        ret.assigned = self.assigned
        ret._annotation = self._annotation
        for attr, val in self.attributes.items():
            ret.attributes[attr] = val.copy()
        return ret


    def modifier_stmts(self, fqn: List[str]) -> List[ast.stmt]:
        ''' Returns a list of statements that have modified this object.  This includes 
        the original assigner statement, any statements that call methods on this object,
        and any modifier statements for attributes of this object.'''
        ret = list()

        if self._assigner is not None:
            ret.append(self._assigner)
        ret.extend(self.method_callers)

        # If fqn is not empty, the recurse to get a more specific list
        if len(fqn) > 0:
            if fqn[0] not in self.attributes:
                # We haven't seen this attribute before, but it might be created by some method call.  
                # Return whatever modified this object itself.
                return ret
            else:
                return bits.unique_elements(ret + self.attributes[fqn[0]].modifier_stmts(fqn[1:]))

        # fqn is empty, so we need modifiers of this ObjectValue, plus those from any attributes
        ret.extend(self.attribute_assigners)
        for attr in self.attributes.values():
            ret.extend(attr.modifier_stmts([]))
        return bits.unique_elements(ret)

    def loader_stmts(self) -> List[ast.stmt]:
        ''' Returns a list of statements that have loaded this object or any of its attributes.'''
        ret = list(self.loaders)
        for attr in self.attributes.values():
            ret.extend(attr.loader_stmts())
        return ret

    def add_load(self, fqn: List[str], stmt: Optional[ast.stmt]) -> bool:
        ''' Records that this object value has been loaded, and by which statement.  Recurses
        to attributes if necessary.  Returns True if the fqn was found, otherwise False, indicating
        that the fqn was not explicitly set before loading.'''

        ret = True
        self.loaded = True

        if stmt is not None:
            self.loaders.append(stmt)

        # If this is a load of an attribute, we need to keep track of that in the attribute.
        if len(fqn) > 0:
            attr = fqn[0]

            # If the attribute has not been explicitly set, it might still exist on the object.
            # Here we create an attribute to keep track of the fact that it was loaded.
            if attr not in self.attributes:
                self.attributes[attr] = ObjectValue(None, None)
                ret = False
            ret &= self.attributes[attr].add_load(fqn[1:], stmt)
        return ret

    def add_attribute_assignment(self, fqn: List[str], assigner: ast.stmt, value: Optional[ast.expr]) -> None:
        assert(len(fqn) > 0)

        # The value currently stored for this object is no longer valid since one of its attributes has changed
        self._value = None

        attr = fqn[0]
        # The assigner has modified this object.
        self.attribute_assigners.append(assigner)

        if len(fqn) > 1:
            # If the attribute has not been explicitly set, it might still exist on the object.
            # Here we create an attribute to keep track of the fact that it was loaded.
            if attr not in self.attributes: 
                self.attributes[attr] = ObjectValue(None, None)
                self.attributes[attr].assigned = True  # We'll assume that someone has created this attribute.  It can't be from another scope.
            self.attributes[attr].add_attribute_assignment(fqn[1:], assigner, value)
        else:
            self.attributes[attr] = ObjectValue(assigner, value)
           
    def add_method_call(self, fqn: List[str], stmt: ast.stmt) -> None:
        if len(fqn) == 0:
            # This is the method called.  Just keep track that it was loaded/used.
            self.loaded = True
            self.loaders.append(stmt)

        else:
            # If this is the last name, then that name is the method name and the method was called
            # on the current object
            if len(fqn) == 1:
                self.method_callers.append(stmt)

            attr = fqn[0]

            # If the method or attribute has not been explicitly set, it might still exist on the object.
            # Here we create an attribute to keep track of the fact that it was loaded/called.
            if attr not in self.attributes:
                self.attributes[attr] = ObjectValue(None, None)

            self.attributes[attr].add_method_call(fqn[1:], stmt)

    def value(self, fqn: List[str]) -> Optional[ast.AST]:
        if len(fqn) == 0:
            return self._value
        
        if fqn[0] not in self.attributes:
            return None

        return self.attributes[fqn[0]].value(fqn[1:])

    def assigner(self, fqn: List[str]) -> Optional[ast.stmt]:
        if len(fqn) == 0:
            return self._assigner
        
        if fqn[0] not in self.attributes:
            return None

        return self.attributes[fqn[0]].assigner(fqn[1:])

    def annotation(self, fqn: List[str]):
        if len(fqn) == 0:
            return self._annotation
        
        if fqn[0] not in self.attributes:
            return None

        return self.attributes[fqn[0]].annotation(fqn[1:])

    def in_scope(self, fqn: List[str]):
        if len(fqn) == 0 and self.assigned:
            return True
        if fqn[0] in self.attributes:
            return self.attributes[fqn[0]].in_scope(fqn[1:])
        return False
    
    def sub_attributes(self) -> List[str]:
        ret = list(self.attributes.keys())
        ret.extend(bits.glue_list_and_vals([ attr.sub_attributes() for attr in self.attributes.values() ]))
        return ret


class Scope():
    ''' Scope is used by the NodeTraverser to keep track of all variables and function
    parameters currently in scope, plus additional information such as the most
    recently assigned value, and any variables that were referenced that were
    not in this scope at the time.
    '''
    def __init__(self):
        self.parameters: List[str] = list()                            # function parameters defined in this scope
        self.parameter_values: List[ObjectValue] = list()              # Stores parameter ObjectValues in order, in case the parameter name gets bound to another object
        self.parameter_values_loaded: List[ObjectValue] = list()       # Stores values for parameters in the order that they are loaded
        self.vars_loaded: List[str] = list()                           # variable names that have been loaded, in order by first load
        self.vars_stored: List[str] = list()                           # variable names that have been stored, in order by first store
        self.values_loaded: List[ObjectValue] = list()
        self.variables: Dict[str, ObjectValue] = dict()               # Variable names and their currently assigned ObjectValue
        self.object_values: List[ObjectValue] = list()
        self.external_vars: List[str] = list()                         # variables loaded that were not previously stored and are not parameters

        self.report_values: bool = True           # In some cases (eg. while loops) we don't want to report the value of variables.
        self.store_values: bool = True            # In some cases we don't want to store values because they may become incorrect later (eg. while loops)


    def copy(self) -> Scope:
        ret = Scope()
        ret.parameters = list(self.parameters)
        ret.parameter_values = list(self.parameter_values)
        ret.vars_loaded = list(self.vars_loaded)
        ret.vars_stored = list(self.vars_stored)
        ret.values_loaded = list(self.values_loaded)
        for var, val in self.variables.items():
            ret.variables[var] = val.copy()
        for val in self.object_values:
            ret.object_values.append(val.copy())
        ret.external_vars = list(self.external_vars)
        ret.report_values = self.report_values
        ret.store_values = self.store_values
        return ret

    def add_parameter(self, par_name, annotation = None):
        self.parameters.append(par_name)
        parobj = ObjectValue(None, None)
        parobj.assigned = False # TODO: Not sure about this one 
        parobj._annotation = annotation

        self.variables[par_name] = parobj
        self.parameter_values.append(parobj)

    def parameters_loaded(self):
        # Searching over the values_loaded so that we get them in order
        ret = []
        for obj in self.parameter_values_loaded:
            # Get the original name of the parameter
            i = self.parameter_values.index(obj)
            ret.append((self.parameters[i], obj._annotation))
        # We only want each parameter to appear once
        return bits.unique_elements(ret)

    def add_var_assignment(self, varname: str, assigner: ast.stmt, value: Optional[ast.expr])-> None:
        fqn = bits.str_fqn(varname)
        assert(len(fqn) > 0)
        self.vars_stored.append(bits.fqn_str(fqn))

        if len(fqn) == 1:
            self.variables[fqn[0]] = ObjectValue(assigner, value)
        else:
            if fqn[0] not in self.variables:
                # Attempt to assign to an attribute of an object that is not in scope.
                # This can happen when keeping track of an assignment to an attribute in a
                # statement scope.  We need to create an empty object to keep track of the assignment.
                self.variables[fqn[0]] = ObjectValue(None, None)

            self.variables[fqn[0]].add_attribute_assignment(fqn[1:], assigner, value)

    def add_var_load(self, varname: str, stmt: Optional[ast.stmt] = None):
        ''' Adds the given variable name to the scope as a load.  If this name is
        already known as a parameter or variable in this scope, then records this reference
        and returns True. If the name is not in this scope then returns False
        '''
        fqn = bits.str_fqn(varname)

        if not self.in_scope(varname):
            self.external_vars.append(varname)
        if fqn[0] in self.variables and self.variables[fqn[0]] in self.parameter_values:
            self.parameter_values_loaded.append(self.variables[fqn[0]])

        assert(len(fqn) > 0)
        self.vars_loaded.append(fqn[0])
        ret = True

        if fqn[0] not in self.variables:
            self.variables[fqn[0]] = ObjectValue(None, None)
            return False

        self.variables[fqn[0]].add_load(fqn[1:], stmt)
        return ret 
 
    def vars_and_attributes_stored(self) -> List[str]:
        return list(self.vars_stored)

    def unique_vars_and_attributes_stored(self) -> List[str]:
        return bits.unique_elements(self.vars_and_attributes_stored())


    def vars_in_scope(self) -> List[str]:
        return [ var for var, val in self.variables.items() if val.assigned ]

    def unique_vars_in_scope(self) -> Optional[List[str]]:
        ''' Returns a list of variables in scope, given in order by most recent store'''
        return bits.unique_elements(self.vars_in_scope())            

    def vars_and_attributes_in_scope(self) -> Optional[List[str]]:
        return bits.glue_list_and_vals([ self.var_attributes(var) for var in self.variables ])

    def var_attributes(self, var) -> List[str]:
        ret = bits.glue_list_and_vals([ var + '.' + attr for attr in self.variables[var].sub_attributes() ])
        ret.append(var)
        return ret

    def var_value(self, varname: str) -> Optional[ast.AST]:
        fqn = bits.str_fqn(varname)
        assert(len(fqn) > 0)
        if fqn[0] not in self.variables:
            return None
        return self.variables[fqn[0]].value(fqn[1:])

    def var_assigner(self, varname: str, ignore_attribute_assigns = False) -> Optional[ast.stmt]:
        fqn = bits.str_fqn(varname)
        assert(len(fqn) > 0)
        if fqn[0] not in self.variables:
            return None
        return self.variables[fqn[0]].assigner(fqn[1:])

    def var_modifiers(self, varname: str) -> List[ast.stmt]:
        fqn = bits.str_fqn(varname)
        assert(len(fqn) > 0)
        if fqn[0] not in self.variables:
            return []
        return self.variables[fqn[0]].modifier_stmts(fqn[1:])

    def var_annotation(self, varname: str):
        fqn = bits.str_fqn(varname)
        assert(len(fqn) > 0)
        if fqn[0] not in self.variables:
            return None
        return self.variables[fqn[0]].annotation(fqn[1:])

    def in_scope(self, varname: str) -> bool:
        fqn = bits.str_fqn(varname)
        assert(len(fqn) > 0)
        if fqn[0] not in self.variables:
            return False
        return True
        #return self.variables[fqn[0]].in_scope(fqn[1:])

    def names_in_scope(self):
        return self.parameters + self.vars_in_scope()


    def add_method_call(self, varname: str, caller: ast.stmt) -> None:
        if not self.in_scope(varname):
            return

        fqn = bits.str_fqn(varname)
        self.variables[fqn[0]].add_method_call(fqn[1:], caller)
