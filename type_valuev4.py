import copy
import copyreg


from enum import Enum
from intbase import InterpreterBase


# Enumerated type for our different language data types

UNDEFINED = "undefined"

class Type(Enum):
    INT = 1
    BOOL = 2
    STRING = 3
    CLOSURE = 4
    NIL = 5
    OBJECT = 6


class Closure:
    def __init__(self, func_ast, env):
        self.captured_env = copy.deepcopy(env)
        self.func_ast = func_ast
        self.type = Type.CLOSURE

class Object:
    def __init__(self, name = None, proto = None, fields = {}):
        self.name = name
        self.proto = proto
        self.fields = fields
        self.type = Type.OBJECT

    

    def set_field(self, key, value):
        self.fields[key] = value

    def set_proto(self, porto):
        self.proto = porto

    def get_proto(self):
        return self.proto

    def get_field(self, key):
        # recursively goes up the prototype chain to find the value, stop when proto is None, returns "undefined" if not found
        if key in self.fields:
            return self.fields[key]
        elif self.proto is not None and self.proto.value() is not None:
            return self.proto.value().get_field(key)
        else:
            return UNDEFINED

# Represents a value, which has a type and its value
class Value:
    def __init__(self, t, v=None):
        self.t = t
        self.v = v

    def value(self):
        return self.v

    def type(self):
        return self.t

    def set(self, other):
        self.t = other.t
        self.v = other.v

def create_value(val):
    if val == InterpreterBase.TRUE_DEF:
        return Value(Type.BOOL, True)
    elif val == InterpreterBase.FALSE_DEF:
        return Value(Type.BOOL, False)
    elif isinstance(val, int):
        return Value(Type.INT, val)
    elif val == InterpreterBase.NIL_DEF:
        return Value(Type.NIL, None)
    elif isinstance(val, str):
        return Value(Type.STRING, val)


def get_printable(val):

    if val.type() == Type.INT:
        return str(val.value())
    if val.type() == Type.STRING:
        return val.value()
    if val.type() == Type.BOOL:
        if val.value() is True:
            return "true"
        return "false"
    if val.type() == Type.OBJECT:
        fval = val.value()
        ffields = "{"
        for k, v in fval.fields.items():
            if v.type() == Type.OBJECT:
                ffields += f" {k} : {(v)}, "
            else: ffields += f" {k} : {get_printable(v)}, "
        ffields += "}"
        fval = f"name({fval.name}) | fields({ffields}) | proto({fval.proto})"
        return fval
    
    if val.type() == Type.CLOSURE:
        fval = val.value()
        fenv = fval.captured_env
        fenv_str = "{\n\t\t"
        for k, v in fenv:
            fenv_str += f"{k} : {get_printable(v)}, \n\t"
        fenv_str += "}"
        fval = f"\n\tenv({fenv_str})\n\t|\n\tfunc(\n\t\t{fval.func_ast}\n\t)\n"
        return fval
    return None