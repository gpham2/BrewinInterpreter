# The EnvironmentManager class keeps a mapping between each variable name (aka symbol)
# in a brewin program and the Value object, which stores a type, and a value.
import copy
from type_valuev2 import Value, Type
 

class EnvironmentManager:
    def __init__(self):
        self.environment = [{}]

    # returns a VariableDef object
    def getIndex(self, symbol):
         for i, env in enumerate(reversed(self.environment)):
            for k, v in env.items():
                if symbol == k:
                  
                    if v.type() != Type.REF :
                        return len(self.environment) - i - 1
                    elif v.value().get("name") != symbol: 
                        return len(self.environment) - i - 1

    def get(self, symbol):
        # for env in reversed(self.environment):
        #     if symbol in env:
        #         return env[symbol]

        # return None
        for env in reversed(self.environment):
            for k, v in env.items():
                if symbol == k:
                  
                    if v.type() != Type.REF :
                        return v
                    elif v.value().get("name") != symbol: 
                        return v
                    

    # def getAbove(self, symbol, symbolAbove = None):
        # index = -1
        # for i, env in enumerate(self.environment):
        #     break_flag = False
        #     for k, v in env.items():
        #         if symbol == k:
        #             index = i
        #         elif symbolAbove and symbolAbove == k:
        #             break_flag = True
        #             break
        #     if break_flag:
        #         break
        #             # if v.type() != Type.REF:
        #             #     return v
        #             # elif v.value().get("name") != symbolAbove:
        #             #     return v
        # if index != -1:
        #     return self.environment[index][symbol]

    def getSymbolIndex(self, symbol, index):
        print("index: " + str(index))
        print("symbol: " + str(symbol))
        print("env: " + str(self.environment[index]))
        print("env[symbol]: " + str(self.environment[index][symbol]))

        return self.environment[index][symbol]

                 
                        
    
    
    def getRef(self, symbol):
        for env in reversed(self.environment):
            if symbol in env:
                return env[symbol]

        return None
    
   

    def set(self, symbol, value):
        for env in reversed(self.environment):
            if symbol in env:
                env[symbol] = value
                return

        # symbol not found anywhere in the environment
        self.environment[-1][symbol] = value

    # create a new symbol in the top-most environment, regardless of whether that symbol exists
    # in a lower environment
    def create(self, symbol, value):
        self.environment[-1][symbol] = value

    # attach symbol and value to index 0 of environment
    def attach(self, symbol, value):
        self.environment[0][symbol] = value

    # used when we enter a nested block to create a new environment for that block
    def push(self):
        self.environment.append({})  # [{}] -> [{}, {}]

    # used when we exit a nested block to discard the environment for that block
    def pop(self):
        self.environment.pop()

    def printEnv(self):
        for i, e in enumerate(self.environment):
            # for symbol in env:
            #     try:
            #         print(symbol, env[symbol].value())
            #     except:
            #         print(symbol, env[symbol])
            print("index: " + str(i))
            for symbol, value in e.items():

                try:
                    print(str(symbol) + " : " + str(value.value()))
                except:
                    print(symbol, value)
            
            print()
    

    def flatten_env_to_dict(self):
        copy_env = copy.deepcopy(self.environment)
        flattened_env = {}
        for e in copy_env:
            for k in e:
                flattened_env[k] = e[k]
        print(flattened_env)
        return flattened_env

   
            
                
