import copy
from enum import Enum

from brewparse import parse_program
from env_v2 import EnvironmentManager
from intbase import InterpreterBase, ErrorType
from type_valuev2 import Type, Value, create_value, get_printable
from type_function import FunctionNode


class ExecStatus(Enum):
    CONTINUE = 1
    RETURN = 2

UNIQUE = "GIANGLAMBDA"

# Main interpreter class
class Interpreter(InterpreterBase):
    # constants
    NIL_VALUE = create_value(InterpreterBase.NIL_DEF)
    TRUE_VALUE = create_value(InterpreterBase.TRUE_DEF)
    BIN_OPS = {"+", "-", "*", "/", "==", "!=", ">", ">=", "<", "<=", "||", "&&"}

    # methods
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)
        self.trace_output = trace_output
        self.__setup_ops()
        self.lambda_count = 0

    def printP(self, content = None):
        if self.trace_output:
            if content == None: 

                print("")
            else:
                print(str(content))

    # run a program that's provided in a string
    # usese the provided Parser found in brewparse.py to parse the program
    # into an abstract syntax tree (ast)
    def run(self, program):
        ast = parse_program(program)
        self.printP(ast)
        self.printP()

        self.env = EnvironmentManager()
        self.__set_up_function_table(ast)
        main_func = self.__get_func_by_name("main", 0)
        self.__run_statements(main_func.get("statements"))

    def print_func_table(self):
        if self.trace_output == False:
            return
        print("func table is: ")
        for func_name in self.func_name_to_ast:
            for num_params in self.func_name_to_ast[func_name]:
                print(f"Function {func_name} with {num_params} params")
        print()


    def __set_up_function_table(self, ast):
        self.func_name_to_ast = {}
        for func_def in ast.get("functions"):
            func_name = func_def.get("name")
            num_params = len(func_def.get("args"))
            if func_name not in self.func_name_to_ast:
                self.func_name_to_ast[func_name] = {}
            self.func_name_to_ast[func_name][num_params] = func_def
        self.print_func_table()


        # putting functions into enviroment
        # for func_def in ast.get("functions"):
        #     func_name = func_def.get("name")
        #     args = func_def.get("args")
        #     statements = func_def.get("statements")
        #     val = FunctionNode({}, args, statements)
        #     self.env.create(func_name, val)

    

    def __get_func_by_name(self, name, num_params, var = False):


        # finds name in env 
        name = self.__resolve_ref(name)
        self.printP("name is: " + name)

        if name not in self.func_name_to_ast:

            # if it is a lambda
            check = self.env.get(name)
            
            # MARK
            if check and check.type() == Type.LAMBDA:     
                if len(check.value().get("params")) != num_params:
                    super().error(ErrorType.TYPE_ERROR, f"Lambda {name} takes wrong number of params")
                return check

                
            

            # if name is in env, but not in func table, we return NameError
            if self.env.get(name):
                super().error(ErrorType.TYPE_ERROR, f"Variable {name} is not a function")

            self.printP("supershy")
            super().error(ErrorType.NAME_ERROR, f"Function {name} not found")
        candidate_funcs = self.func_name_to_ast[name]

        if var:
            if len(candidate_funcs) > 1:
                super().error(
                    ErrorType.NAME_ERROR,
                    f"Cannot assign function {name} taking to variable since there are multiple functions with that name",
                )
            if len(candidate_funcs) == 0:
                super().error(
                    ErrorType.NAME_ERROR,
                    f"Function {name} not found",
                )
            return candidate_funcs
        

        # MARK
        elif num_params not in candidate_funcs:
            if self.env.get(name):
                super().error(ErrorType.TYPE_ERROR, f"Variable {name} takes wrong number of params")
            super().error(
                ErrorType.NAME_ERROR,
                f"Function {name} taking {num_params} params not found",
            )
        
        return candidate_funcs[num_params]
  

    def __run_statements(self, statements):
        self.env.push()
        for statement in statements:
            if self.trace_output:
                self.printP('printing statement')
                self.printP(statement)
                if self.trace_output:
                    self.printP(self.env.printEnv())
                self.printP()
            status = ExecStatus.CONTINUE
            if statement.elem_type == InterpreterBase.FCALL_DEF:
                self.__call_func(statement)
            elif statement.elem_type == "=":
                self.__assign(statement)
            elif statement.elem_type == InterpreterBase.RETURN_DEF:
                status, return_val = self.__do_return(statement)
            elif statement.elem_type == Interpreter.IF_DEF:
                status, return_val = self.__do_if(statement)
            elif statement.elem_type == Interpreter.WHILE_DEF:
                status, return_val = self.__do_while(statement)

            if status == ExecStatus.RETURN:
                self.printP("returning")
                self.env.pop()
                return (status, return_val)

        self.env.pop()
        return (ExecStatus.CONTINUE, Interpreter.NIL_VALUE)

    def __call_func(self, call_node):
        func_name = call_node.get("name")
        if func_name == "print":
            return self.__call_print(call_node)
        if func_name == "inputi":
            return self.__call_input(call_node)
        if func_name == "inputs":
            return self.__call_input(call_node)

        actual_args = call_node.get("args")
        func_ast = self.__get_func_by_name(func_name, len(actual_args))
        # print("actual parge")
        # for arg in actual_args:
        #     print(arg)

        formal_args = None
        if func_ast.type() == Type.LAMBDA:
            formal_args = func_ast.value().get("params")
            # print("HEHE HAHA")
        else: 
            formal_args = func_ast.get("args")
        
        # print('formal parge')
        # for arg in formal_args:
        #     print(arg)
        # print("END")
  
        if len(actual_args) != len(formal_args):
            super().error(
                ErrorType.NAME_ERROR,
                f"Function {func_ast.get('name')} with {len(actual_args)} args not found",
            )
        self.env.push()

        # print()
        # print(formal_args[0].elem_type)
        # print(formal_args[0])
        # print(actual_args[0])
        # print("END\n")

        for formal_ast, actual_ast in zip(formal_args, actual_args):
            
            result = None
            if formal_ast.elem_type == InterpreterBase.REFARG_DEF:
                result = Value(Type.REF, actual_ast)
                self.printP("0")
            else: 
                self.printP("1")
                self.printP(actual_ast)
                result = copy.deepcopy(self.__eval_expr(actual_ast))
                self.printP(result.value())

            arg_name = formal_ast.get("name")
            self.env.create(arg_name, result)
        _, return_val = self.__run_statements(func_ast.get("statements"))
        self.printP()
        self.printP()
        self.env.pop()
        return return_val

    def __call_print(self, call_ast):
        output = ""
        for arg in call_ast.get("args"):
            result = self.__eval_expr(arg)  # result is a Value object
            output = output + get_printable(result)
        super().output(output)
        return Interpreter.NIL_VALUE

    def __call_input(self, call_ast):
        args = call_ast.get("args")
        if args is not None and len(args) == 1:
            result = self.__eval_expr(args[0])
            super().output(get_printable(result))
        elif args is not None and len(args) > 1:
            super().error(
                ErrorType.NAME_ERROR, "No inputi() function that takes > 1 parameter"
            )
        inp = super().get_input()
        if call_ast.get("name") == "inputi":
            return Value(Type.INT, int(inp))
        if call_ast.get("name") == "inputs":
            return Value(Type.STRING, inp)

    def __assign(self, assign_ast):
        var_name = assign_ast.get("name")
        value_obj = self.__eval_expr(assign_ast.get("expression"))
        self.printP("running assignment")
        self.printP("var name: " + var_name)
        refers_to = self.__resolve_ref(var_name)
        if value_obj.type() == Type.FUNCTION:
            # value_obj = Value(Type.REF, {"elem_type": "func", "name": value_obj.value().get("name")})
            value_obj = Value(Type.REF, {"elem_type": "func", "name": value_obj.value().get("name")})
        if value_obj.type() == Type.LAMBDA:
            print("VALUEOBJECT")
            print(value_obj)
            self.env.attach(refers_to, value_obj)
            return
        self.env.set(refers_to, value_obj)
        if self.trace_output:
            self.env.printEnv()
        

    
    def __resolve_ref(self, var_name):
        self.printP("resolving ref")
        if self.trace_output:
            self.env.printEnv()
        curr = self.env.get(var_name)
        refers_to = var_name
        self.printP("var name: " + var_name)
        while curr and curr.type() == Type.REF:
            self.printP("cycle1")
            self.printP(curr)
            refers_to = curr.value().get("name")
            # curr = self.env.get(refers_to)
            # if curr is None:
            #     super().error(ErrorType.NAME_ERROR, f"Variable {refers_to} not found")


            for env in reversed(self.env.environment):
                if refers_to in env:
                    refers_to_val = env[refers_to]
                    if refers_to_val.type() == Type.REF and refers_to_val.value().get("name") == refers_to:
                        continue
                    curr = env[refers_to]
                
        return refers_to
        
        
        


    def __eval_expr(self, expr_ast):
        # print("here expr")
        # print("type: " + str(expr_ast.elem_type))
        if expr_ast.elem_type == InterpreterBase.NIL_DEF:
            # print("getting as nil")
            return Interpreter.NIL_VALUE
        if expr_ast.elem_type == InterpreterBase.INT_DEF:
            return Value(Type.INT, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.STRING_DEF:
            # print("getting as str")
            return Value(Type.STRING, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.BOOL_DEF:
            return Value(Type.BOOL, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.VAR_DEF:
            self.printP("HERE")
            var_name = expr_ast.get("name")
            self.printP(var_name)
            self.printP(expr_ast)
            # var name = a
            # if var is just a clasic value
            val = self.env.get(var_name)
            self.printP("nothing1")
            # look for vars that are references
            while val and val.type() == Type.REF:
                var_name = val.value().get("name")
                val = self.env.get(var_name)
                self.printP("should be here")
              
            self.printP("nothing2")
            
            if val is None:
                function_found = self.__get_func_by_name(var_name, 0, True)
                self.printP("FUNC")
                self.printP(function_found)

                # get key of function
                function_details = list(function_found.values())[0]
                val = FunctionNode({}, function_details.get("args"), function_details.get("statements"), function_details.get("name"))
                self.env.attach( function_details.get("name"), val)
                self.printP("FUNC2")
                if self.trace_output:
                    self.env.printEnv()
                val =  Value(Type.REF, {"elem_type": "func", "name": var_name})
                # self.env.create(var_name, Value(Type.REF, {"elem_type": "func", "name": var_name}))
                
            if val is None:
                super().error(ErrorType.NAME_ERROR, f"Variable {var_name} not found")
            return val
        if expr_ast.elem_type == InterpreterBase.FCALL_DEF:
            return self.__call_func(expr_ast)
        if expr_ast.elem_type in Interpreter.BIN_OPS:
            return self.__eval_op(expr_ast)
        if expr_ast.elem_type == Interpreter.NEG_DEF:
            return self.__eval_unary(expr_ast, Type.INT, lambda x: -1 * x)
        if expr_ast.elem_type == Interpreter.NOT_DEF:
            return self.__eval_unary(expr_ast, Type.BOOL, lambda x: not x)
        if expr_ast.elem_type == Interpreter.LAMBDA_DEF:
            self.printP("LAMBDA")
            self.lambda_count += 1
            val = FunctionNode(copy.deepcopy(self.env), expr_ast.get("args"), expr_ast.get("statements"), str(UNIQUE) + str(self.lambda_count), Type.LAMBDA)
            return val
        

    

    def __eval_op(self, arith_ast):
        left_value_obj = self.__eval_expr(arith_ast.get("op1"))
        right_value_obj = self.__eval_expr(arith_ast.get("op2"))
        if not self.__compatible_types(
            arith_ast.elem_type, left_value_obj, right_value_obj
        ):
            super().error(
                ErrorType.TYPE_ERROR,
                f"Incompatible types for {arith_ast.elem_type} operation",
            )

        # perform coercion here
        left_coerced, right_coerced = self.__coerce_types(left_value_obj, right_value_obj, arith_ast.elem_type)

        if arith_ast.elem_type not in self.op_to_lambda[left_coerced.type()]:
            super().error(
                ErrorType.TYPE_ERROR,
                f"Incompatible operator {arith_ast.elem_type} for type {left_value_obj.type()}",
            )
        f = self.op_to_lambda[left_coerced.type()][arith_ast.elem_type]
        return f(left_coerced, right_coerced)

    def __compatible_types(self, oper, obj1, obj2):
        # DOCUMENT: allow comparisons ==/!= of anything against anything
        if oper in ["==", "!="]:
            return True
        
        # Compat operation between INT and BOOL
        if obj1.type() == Type.INT and obj2.type() == Type.BOOL or obj1.type() == Type.BOOL and obj2.type() == Type.INT:
                return True
        return obj1.type() == obj2.type()
    
    

    def __eval_unary(self, arith_ast, t, f):
        value_obj = self.__eval_expr(arith_ast.get("op1"))
        coerced_obj, _ = self.__coerce_types(value_obj, None, arith_ast.elem_type)
        if coerced_obj.type() != t:
            super().error(
                ErrorType.TYPE_ERROR,
                f"Incompatible type for {arith_ast.elem_type} operation",
            )
        return Value(t, f(coerced_obj.value()))


    def __coerce_types(self, obj1, obj2, oper):
        
        if oper in ["==", "!="]:
            if obj1 and obj1.type() == Type.INT and obj2 and obj2.type() == Type.BOOL:
                return (Value(Type.BOOL, obj1.value() != 0), obj2)
                
            elif obj1 and obj1.type() == Type.BOOL and obj2 and obj2.type() == Type.INT:
                return (obj1, Value(Type.BOOL, obj2.value() != 0))
            
            
        elif oper in ["+", "-", "*", "/"]:
            if obj1 and obj1.type() == Type.BOOL:
                obj1 = Value(Type.INT, 1 if obj1.value() else 0)
            if obj2 and obj2.type() == Type.BOOL:
                obj2 = Value(Type.INT, 1 if obj2.value() else 0)

        elif oper in ["&&", "||", "!", "conditional"]:
            if obj1 and obj1.type() == Type.INT:
                obj1 = Value(Type.BOOL, obj1.value() != 0)
            if obj2 and obj2.type() == Type.INT:
                obj2 = Value(Type.BOOL, obj2.value() != 0)

        
           
        return (obj1, obj2)


    def __setup_ops(self):
        self.op_to_lambda = {}
        # set up operations on integers
        self.op_to_lambda[Type.INT] = {}
        self.op_to_lambda[Type.INT]["+"] = lambda x, y: Value(
            x.type(), x.value() + y.value()
        )
        self.op_to_lambda[Type.INT]["-"] = lambda x, y: Value(
            x.type(), x.value() - y.value()
        )
        self.op_to_lambda[Type.INT]["*"] = lambda x, y: Value(
            x.type(), x.value() * y.value()
        )
        self.op_to_lambda[Type.INT]["/"] = lambda x, y: Value(
            x.type(), x.value() // y.value()
        )
        self.op_to_lambda[Type.INT]["=="] = lambda x, y: Value(
            Type.BOOL, x.type() == y.type() and x.value() == y.value()
        )
        self.op_to_lambda[Type.INT]["!="] = lambda x, y: Value(
            Type.BOOL, x.type() != y.type() or x.value() != y.value()
        )
        self.op_to_lambda[Type.INT]["<"] = lambda x, y: Value(
            Type.BOOL, x.value() < y.value()
        )
        self.op_to_lambda[Type.INT]["<="] = lambda x, y: Value(
            Type.BOOL, x.value() <= y.value()
        )
        self.op_to_lambda[Type.INT][">"] = lambda x, y: Value(
            Type.BOOL, x.value() > y.value()
        )
        self.op_to_lambda[Type.INT][">="] = lambda x, y: Value(
            Type.BOOL, x.value() >= y.value()
        )
        #  set up operations on strings
        self.op_to_lambda[Type.STRING] = {}
        self.op_to_lambda[Type.STRING]["+"] = lambda x, y: Value(
            x.type(), x.value() + y.value()
        )
        self.op_to_lambda[Type.STRING]["=="] = lambda x, y: Value(
            Type.BOOL, x.value() == y.value()
        )
        self.op_to_lambda[Type.STRING]["!="] = lambda x, y: Value(
            Type.BOOL, x.value() != y.value()
        )
        #  set up operations on bools
        self.op_to_lambda[Type.BOOL] = {}
        self.op_to_lambda[Type.BOOL]["&&"] = lambda x, y: Value(
            x.type(), x.value() and y.value()
        )
        self.op_to_lambda[Type.BOOL]["||"] = lambda x, y: Value(
            x.type(), x.value() or y.value()
        )
        self.op_to_lambda[Type.BOOL]["=="] = lambda x, y: Value(
            Type.BOOL, x.type() == y.type() and x.value() == y.value()
        )
        self.op_to_lambda[Type.BOOL]["!="] = lambda x, y: Value(
            Type.BOOL, x.type() != y.type() or x.value() != y.value()
        )

        #  set up operations on nil
        self.op_to_lambda[Type.NIL] = {}
        self.op_to_lambda[Type.NIL]["=="] = lambda x, y: Value(
            Type.BOOL, x.type() == y.type() and x.value() == y.value()
        )
        self.op_to_lambda[Type.NIL]["!="] = lambda x, y: Value(
            Type.BOOL, x.type() != y.type() or x.value() != y.value()
        )

        self.op_to_lambda[Type.FUNCTION] = {}
        self.op_to_lambda[Type.FUNCTION]["=="] = lambda x, y: Value(
            Type.BOOL, x.type() == y.type() and x.value() == y.value()
        )
        self.op_to_lambda[Type.FUNCTION]["!="] = lambda x, y: Value(
            Type.BOOL, x.type() != y.type() or x.value() != y.value()
        )

        self.op_to_lambda[Type.REF] = {}
        self.op_to_lambda[Type.REF]["=="] = lambda x, y: Value(
            Type.BOOL, x.type() == y.type() and x.value()['name'] == y.value()['name'] 
        )

        self.op_to_lambda[Type.REF]["!="] = lambda x, y: Value(
            Type.BOOL, x.type() != y.type() or x.value()['name'] != y.value()['name'] 
        )

    def __do_if(self, if_ast):
        cond_ast = if_ast.get("condition")
        result = self.__coerce_types(self.__eval_expr(cond_ast), None, "conditional")[0]
        self.printP("in if, condition result is: ")
        self.printP(result)
        self.printP()
        if result.type() != Type.BOOL:
            super().error(
                ErrorType.TYPE_ERROR,
                "Incompatible type for if condition",
            )
        if result.value():
            statements = if_ast.get("statements")
            status, return_val = self.__run_statements(statements)
            return (status, return_val)
        else:
            else_statements = if_ast.get("else_statements")
            if else_statements is not None:
                status, return_val = self.__run_statements(else_statements)
                return (status, return_val)

        return (ExecStatus.CONTINUE, Interpreter.NIL_VALUE)

    def __do_while(self, while_ast):
        cond_ast = while_ast.get("condition")
        run_while = Interpreter.TRUE_VALUE
        while run_while.value():
            run_while = self.__coerce_types(self.__eval_expr(cond_ast), None, "conditional")[0]
            if run_while.type() != Type.BOOL:
                super().error(
                    ErrorType.TYPE_ERROR,
                    "Incompatible type for while condition",
                )
            if run_while.value():
                statements = while_ast.get("statements")
                status, return_val = self.__run_statements(statements)
                if status == ExecStatus.RETURN:
                    return status, return_val

        return (ExecStatus.CONTINUE, Interpreter.NIL_VALUE)

    def __do_return(self, return_ast):
        expr_ast = return_ast.get("expression")
        if expr_ast is None:
            return (ExecStatus.RETURN, Interpreter.NIL_VALUE)
        value_obj = copy.deepcopy(self.__eval_expr(expr_ast))
        return (ExecStatus.RETURN, value_obj)
