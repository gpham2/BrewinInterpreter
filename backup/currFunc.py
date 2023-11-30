from type_valuev2 import Value, Type



# function node is a subclass of Value
class FunctionNode (Value):
    def __init__(self, env, params, body, name):

        # object of env, params, and body
        value = {
            "name": name,
            "env": env,
            "params": params,
            "body": body
        }
        super().__init__(Type.FUNCTION, value)

    # create to string
    def __str__(self):
        print("printing function node : " + self.v["name"]) 

        print("env: ", self.v["env"])

        print("params: ")
        for param in self.v["params"]:
            print(param.get("name"), end=" ")
        print()
        print("body: ")
        for line in self.v["body"]:
            print(line)
        print()

    def execute(self, args):
        # Create a new environment for the function call
        # new_env = Environment(self.env)

        # # Add the parameters to the new environment
        # for i in range(len(self.params)):
        #     new_env.add(self.params[i], args[i])

        # # Execute the body of the function in the new environment
        # return self.body.execute(new_env)
        return 0