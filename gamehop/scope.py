from __future__ import annotations
from typing import Optional, List, Union
import ast
from . import bits

class NoValue():
    '''Used in Scope() objects to indicate that a variable has no value assigned'''

class Store():
    def __init__(self, var, value, assigner, store_type, previous_assigner, annotation) :
        self.var = var
        self.value = value
        self.assigner = assigner 
        self.store_type = store_type
        self.annotation = annotation
        self.previous_assigner = previous_assigner

class Scope():
    ''' Scope is used by the NodeTraverser to keep track of all variables and function
    parameters currently in scope, plus additional information such as the most
    recently assigned value, and any variables that were referenced that were
    not in this scope at the time.
    '''
    def __init__(self):
        self.parameters = list()            # function parameters defined in this scope
        self.vars_loaded = list()           # variables that have been loaded, in order by first load
        self.load_type = dict()             # type of load (attribute or whatever).  key = var, value = load type
        self.external_vars = list()         # variables loaded that were not previously stored and are not parameters
        self.parameters_loaded = list()     # parameters that have been read by a load, in order by first load
        self.parameter_annotations = dict() # most recent type annotation for a variable
        self.stores = list()                # list of Store objects recording the order that variables are written to
        self.report_values = True           # In some cases (eg. while loops) we don't want to report the value of variables.
        self.store_values = True            # In some cases we don't want to store values because they may become incorrect later (eg. while loops)

    def add_parameter(self, par_name, annotation = NoValue()):
        self.parameters.append(par_name)
        self.parameter_annotations[par_name] = annotation

    def add_var_store(self, varname, value, assigner: ast.stmt, store_type = None, annotation = None):
        if not self.store_values:
            value = NoValue()

        old_assigner = None
        if store_type is None:
            if self.in_scope(varname):
                store_type = 'overwrite'
                old_assigner = self.var_assigner(varname)

        self.stores.append(Store(varname, value, assigner, store_type, old_assigner, annotation))

        # If an object has been overwritten, then we need to invalidate the values of any of its attributes.
        # For this to work correctly, we depend on the fact that object stores are added before stores of
        # attributes
        if store_type != 'attribute':
            for v in (v for v in self.vars_in_scope() if v.startswith(varname + '.')):
                old_assigner = self.var_assigner(v)
                self.stores.append(Store(v, NoValue(), assigner, store_type, old_assigner, None))

    def add_var_load(self, varname, load_type = None):
        ''' Adds the given variable name to the scope, treat as a load.  If this name is
        already known as a parameter or variable in this scope, then records this reference
        and returns True. If the name is not in this scope then returns False
        '''
        # variables stored will always assigned after the start of the function, so if this
        # has happened then a Load refers to the stored variable, not a parameter
        self.load_type[varname] = load_type
        if self.in_scope(varname):
            bits.append_if_unique(self.vars_loaded, varname)
            return True
        elif varname in self.parameters:
            bits.append_if_unique(self.parameters_loaded, varname)
            return True
        else:
            # the variable is not in scope
            bits.append_if_unique(self.external_vars, varname)
            return False

    def vars_in_scope(self) -> List[str]:
        return [ s.var for s in self.stores ] 

    def unique_vars_in_scope(self) -> Optional[List[str]]:
        ''' Returns a list of variables in scope, given in order by most recent store'''
        stores = self.vars_in_scope()
        stores.reverse()
        stores = bits.unique_elements(stores)
        stores.reverse()
        return stores

    def var_store(self, var: str) -> Optional[Store]:
        matching_stores = [ s for s in self.stores if s.var == var ]
        if len(matching_stores) > 0:
            return matching_stores[-1]
        return None

    def var_value(self, var:str) -> Union[ast.expr, NoValue, None]:
        store = self.var_store(var)
        if store:
            if self.report_values:
                return store.value
            else:
                return NoValue()
        if var in self.parameters:
            return NoValue()

        return None

    def var_assigner(self, var:str, ignore_attribute_assigns = False) -> Optional[ast.stmt]:
        if ignore_attribute_assigns:
            stores = [ s for s in self.stores if s.var == var and s.store_type != 'attribute' ]
            if len(stores) > 0:
                store = stores[-1]
            else:
                store = None
        else:
            store = self.var_store(var)

        if store:
            return store.assigner

        return None
 
    def var_annotation(self, var:str):
        store = self.var_store(var)
        if store:
            return store.annotation

        return None

    def var_store_type(self, var:str) -> Optional[str]:
        store = self.var_store(var)
        if store:
            return store.store_type

        return None
    def var_load_type(self, var:str) -> Optional[str]:
        if var in self.load_type:
            return self.load_type[var]

        return None

    def in_scope(self, varname):
        return self.var_store(varname) is not None

    def names_in_scope(self):
        return self.parameters + self.vars_in_scope()

    def copy(self) -> Scope:
        ret = Scope()
        ret.stores = self.stores[:]
        ret.parameters = self.parameters[:]
        ret.vars_loaded = self.vars_loaded[:]
        ret.external_vars = self.external_vars[:]
        ret.parameters_loaded = self.parameters_loaded[:]
        ret.parameter_annotations = dict(self.parameter_annotations)
        return ret

    def diff(self, other: Scope) -> Scope:
        '''Return a Scope object whose various lists are those of the
        current object with elements from the other object's lists removed'''
        ret = Scope()
        ret.stores = [ s for s in self.stores if s not in other.stores ]
        ret.parameters = [ p for p in self.parameters if p not in other.parameters ]
        ret.vars_loaded = [ p for p in self.vars_loaded if p not in other.vars_loaded ]
        ret.external_vars = [ p for p in self.external_vars if p not in other.external_vars ]
        ret.parameters_loaded = [ p for p in self.parameters_loaded if p not in other.parameters_loaded ]
        ret.parameter_annotations = { k: v for k,v in self.parameter_annotations.items() if k not in other.parameter_annotations }
        return ret
