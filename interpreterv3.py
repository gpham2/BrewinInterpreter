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
        self.id = 0
        

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
                print(self.func_name_to_ast[func_name][num_params])
                print()
        print()


    def __set_up_function_table(self, ast):
        self.func_name_to_ast = {}
        for func_def in ast.get("functions"):
            # print("func def")
            # print(func_def)
            func_name = func_def.get("name")
            num_params = len(func_def.get("args"))
            if func_name not in self.func_name_to_ast:
                self.func_name_to_ast[func_name] = {}
            # MARK 2
            self.func_name_to_ast[func_name][num_params] = func_def
        self.print_func_table()


    

    def __get_func_by_name(self, name, num_params, var = False):


        # finds name in env 
        name = self.__resolve_ref(name)
        if name not in self.func_name_to_ast:
            # if name is in env, but not in func table, we return NameError
            pass_flag = False
            func = self.env.get(name)
            if func and (func.type() == Type.FUNCTION or func.type() == Type.LAMBDA):
                lead = func.value().get("name")
                if lead in self.func_name_to_ast:
                        pass_flag = True
                        name = lead
            if pass_flag == False:
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
  
    
    
    def __print_flattened_env(self, flattened_env):
        print("printing flattened env")
        for k in flattened_env:
            print(k, flattened_env[k].value())
        print()

    def __run_statements(self, statements, lambda_env = None, func_name = None):
        self.env.push()

        if lambda_env is not None:
            # we transver the lambda env to the current env's end
            # MARK 6

            # self.__print_flattened_env(lambda_env)

            params_name = [] 
            for k in lambda_env:
                # getting list of args
                find = self.env.get(func_name)
                lambda_params = find.value().get("params")
                   
                for param in lambda_params:
                    params_name.append(param.get("name"))
                    self.printP("params to avoid")
                    self.printP(params_name)
                if k in params_name:
                    self.printP("skipping because param")
                    self.printP(k)
                    continue
                self.printP("creating")
                self.printP(k)
                self.env.create(k, lambda_env[k]) 
                if self.trace_output:
                    self.env.printEnv()


            if self.trace_output:
                self.env.printEnv()
            
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

            # updating status of closure
            if lambda_env is not None and func_name is not None:
                updated_lambda_env = {}
                for k in lambda_env:
                    updated_lambda_env[k] = self.env.get(k)
            
                find = self.env.get(func_name)
                self.env.set(func_name, Value(Type.FUNCTION, {"name": find.value().get("name"), "env": updated_lambda_env, "params": find.value().get("params"), "body": find.value().get("body"), "id": find.value().get("id")}))


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
        
        # tries to find if lambda MARK 3
        self.printP("TRYING FIND LAMBDA")
        actual_args = call_node.get("args")
        #MARK 5
        
        func_ast = self.__get_func_by_name(func_name, len(actual_args))
        # print(func_ast)
        formal_args = func_ast.get("args")
  
        if len(actual_args) != len(formal_args):
            super().error(
                ErrorType.NAME_ERROR,
                f"Function {func_ast.get('name')} with {len(actual_args)} args not found",
            )
        self.env.push()


        # if what we are running is a lambda
        lambda_env = None
        resolved_name = None
        if func_ast.elem_type == Interpreter.LAMBDA_DEF:
            #  we get the lambda env
            resolved_name = self.__resolve_ref(func_name)
            # print(func_ast)
            # print("AHWHEQHEHQWhe")
            # print(resolved_name)
            # print(resolved_name)
            # print(self.env.get(resolved_name))
            lambda_env = self.env.get(resolved_name).value().get("env")
            # print("lambda env")
            # print(lambda_env)
            # self.env.printEnv()
            

        for formal_ast, actual_ast in zip(formal_args, actual_args):
            
            # MARK 7
            result = None
            if formal_ast.elem_type == InterpreterBase.REFARG_DEF:
                result = Value(Type.REF, actual_ast)
                print("HERE?")
                print (result.value())
                if actual_ast.elem_type == InterpreterBase.VAR_DEF:
                    name = result.value().get("name")
                    index = self.env.getIndex(name)
                    result = Value(Type.REF, {"elem_type": "var", "name": name, "index": index})
                
                
                if actual_ast.elem_type == InterpreterBase.LAMBDA_DEF:
                    lambda_name = str(UNIQUE) + str(self.lambda_count)
                    val = FunctionNode(self.env.flatten_env_to_dict(), actual_ast.get("args"), actual_ast, lambda_name, Type.LAMBDA, self.id)
                    self.id += 1
                    self.env.attach( lambda_name, val)
                    self.lambda_count += 1
                    # self.env.printEnv()

                    func_name = val.value().get("name")
                    num_params = len(val.value().get("params"))
                    func_def = val.value().get("body")
                    if func_name not in self.func_name_to_ast:
                        self.func_name_to_ast[func_name] = {}
                    self.func_name_to_ast[func_name][num_params] = func_def
                    result = Value(Type.REF, {"elem_type": "lambda", "name": lambda_name})
                self.printP("0")
                
            else: 
                self.printP("1")
                self.printP(actual_ast)
                result = copy.deepcopy(self.__eval_expr(actual_ast))
                self.printP(result.value())

            arg_name = formal_ast.get("name")
            self.env.create(arg_name, result)
            if self.trace_output:
                self.env.printEnv()
        _, return_val = self.__run_statements(func_ast.get("statements"), lambda_env, resolved_name)
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

        # MARK 1
        # print("expression is")
        # print(assign_ast.get("expression"))
        value_obj = self.__eval_expr(assign_ast.get("expression"))
        self.printP("running assignment")
        self.printP("var name: " + var_name)
        var_index = self.env.getIndex(var_name)
        refers_to = None
        index = None
        if var_index is None:
            refers_to = self.__resolve_ref(var_name)
        else:
            refers_to, index = self.__resolve_ref(var_name, var_index)
        self.printP("refers to: " + refers_to)
        self.printP("index is: " + str(index))
        self.printP("value obj: ")
        self.printP(value_obj)
        if value_obj.type() == Type.FUNCTION:
            value_obj = Value(Type.REF, {"elem_type": "func", "name": value_obj.value().get("name")})
        if value_obj.type() == Type.LAMBDA:

            # add to env
            # self.env.attach(refers_to, value_obj)
            value_obj = Value(Type.REF, {"elem_type": "lambda", "name": value_obj.value().get("name")})
           
            self.print_func_table()

            if self.trace_output:
                self.env.printEnv()

        self.env.set(refers_to, value_obj)

    
    def __resolve_ref(self, var_name, index = None):
        if self.trace_output:
            # print()
            self.env.printEnv()
        
        curr = self.env.get(var_name)
        if index is not None:
            curr = self.env.getSymbolIndex(var_name, index)
            while curr and curr.type() == Type.REF:
                refers_to = curr.value().get("name")
                index = curr.value().get("index")
                self.printP(curr)
                self.printP(index)
                curr = self.env.getSymbolIndex(refers_to, index)
            
            return refers_to, index


        refers_to = var_name
        # self.printP("var name: " + var_name)
        while curr and curr.type() == Type.REF:
            # self.printP("cycle1")
            self.printP(curr)
            refers_to = curr.value().get("name")
      
            # print("refers to: " + refers_to)
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
        self.printP("evaluating expr")
        self.printP(expr_ast)
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
            self.printP("expression is a var")
            var_name = expr_ast.get("name")

            index = self.env.getIndex(var_name)
            self.printP("indexX is: " + str(index))
            if index is not None:
            
                val = self.env.getSymbolIndex(var_name, index)
                print("valX")
                print(val.value())
                while index and val and val.type() == Type.REF:
                    self.printP("c1")
                    var_name = val.value().get("name")
                    # val = self.env.getSymbolIndex(var_name, index)
                    self.printP("VALUE")
                    self.printP(val.value())
                    index  = val.value().get("index")

                    val = self.env.getSymbolIndex(var_name, index)
                print("final val")
                print(val.value())

                
            # MARK 11
            # self.printP(var_name)
            # self.printP(expr_ast)
            # MARK 10
            # var name = a
            # if var is just a clasic value
            else: 
                val = self.env.get(var_name)
                # look for vars that are references
                while val and val.type() == Type.REF:
                    var_name = val.value().get("name")
                    val = self.env.get(var_name)
                    # print("var name: " + var_name)
                    # print("val: " + str(val))
                
            
              
            
            if val is None:
                function_found = self.__get_func_by_name(var_name, 0, True)
                self.printP("var refers to function")
                self.printP(function_found)
                function_details = list(function_found.values())[0]
                # if function
                val = FunctionNode({}, function_details.get("args"), function_details.get("statements"), function_details.get("name"), Type.FUNCTION, self.id)
                self.id += 1
                self.env.attach( function_details.get("name"), val)
                # if lambda
                self.printP("FUNC2")
                if self.trace_output:
                    self.env.printEnv()
                val =  Value(Type.REF, {"elem_type": "func", "name": var_name, "index": 0})
                # self.env.create(var_name, Value(Type.REF, {"elem_type": "func", "name": var_name}))
                
            if val is None:
                super().error(ErrorType.NAME_ERROR, f"Variable {var_name} not found")
            if index is None:
                return val
            else:
                return val, index
        if expr_ast.elem_type == InterpreterBase.FCALL_DEF:
            return self.__call_func(expr_ast)
        if expr_ast.elem_type in Interpreter.BIN_OPS:
            return self.__eval_op(expr_ast)
        if expr_ast.elem_type == Interpreter.NEG_DEF:
            return self.__eval_unary(expr_ast, Type.INT, lambda x: -1 * x)
        if expr_ast.elem_type == Interpreter.NOT_DEF:
            return self.__eval_unary(expr_ast, Type.BOOL, lambda x: not x)
        if expr_ast.elem_type == Interpreter.LAMBDA_DEF:
            lambda_name = str(UNIQUE) + str(self.lambda_count)
            val = FunctionNode(self.env.flatten_env_to_dict(), expr_ast.get("args"), expr_ast, lambda_name, Type.LAMBDA, self.id)
            self.id += 1
            self.env.attach( lambda_name, val)
            self.lambda_count += 1
            self.env.printEnv()

            func_name = val.value().get("name")
            num_params = len(val.value().get("params"))
            func_def = val.value().get("body")
            if func_name not in self.func_name_to_ast:
                self.func_name_to_ast[func_name] = {}
            self.func_name_to_ast[func_name][num_params] = func_def
            return Value(Type.REF, {"elem_type": "lambda", "name": lambda_name, "index": 0})

        

    

    def __eval_op(self, arith_ast):
        left_value_obj = self.__eval_expr(arith_ast.get("op1"))
        right_value_obj = self.__eval_expr(arith_ast.get("op2"))

        self.printP("left value obj")
        self.printP(left_value_obj)
        # if the returned is a tupple
        index1 = None
        index2 = None
        if type(left_value_obj) == tuple:
            index1 = left_value_obj[1]
            left_value_obj = left_value_obj[0]
            
        if type(left_value_obj) == tuple:
            index2 = right_value_obj[1]
            right_value_obj = right_value_obj[0]
        print("A HERE")
   
        self.printP("right value obj")
        self.printP(right_value_obj)
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

        self.op_to_lambda[Type.LAMBDA] = {}
        self.op_to_lambda[Type.LAMBDA]["=="] = lambda x, y: Value(
            Type.BOOL, x.type() == y.type() and x.value()['name'] == y.value()['name'] 
        )
        self.op_to_lambda[Type.LAMBDA]["!="] = lambda x, y: Value(
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
        if value_obj.type() == Type.FUNCTION:
            # create another functionNode
            newName = str(UNIQUE) + value_obj.value().get("name") + str(self.id)
            value_obj2 = FunctionNode(value_obj.value().get("env"), value_obj.value().get("params"), value_obj.value().get("body"), value_obj.value().get("name"), Type.FUNCTION, self.id)
            self.id += 1
            self.env.attach(newName, value_obj2)

            # make currentValue Object a reference to the new functionNode
            value_obj = Value(Type.REF, {"elem_type": "func", "name": newName, "index": 0})
        elif value_obj.type() == Type.LAMBDA:
            newName = str(UNIQUE) + str(self.lambda_count)
            self.lambda_count += 1
            value_obj2 = FunctionNode(value_obj.value().get("env"), value_obj.value().get("params"), value_obj.value().get("body"), newName, Type.FUNCTION, self.id)
            self.id += 1
            self.env.attach(newName, value_obj2)


            value_obj = Value(Type.REF, {"elem_type": "lambda", "name": newName, "index": 0})

        if self.trace_output:
            self.env.printEnv()

        return (ExecStatus.RETURN, value_obj)