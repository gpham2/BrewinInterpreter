from type_valuev2 import Value, Type



# function node is a subclass of Value
class FunctionNode (Value):
    def __init__(self, env, params, body, name, type = Type.FUNCTION, id  = -1):

        # object of env, params, and body
        value = {
            "name": name,
            "env": env,
            "params": params,
            "body": body,
            "id": id
        }
        super().__init__(type, value)

    # create to string
    def __str__(self):
        string_representation = ""
        string_representation += "printing function node : " + self.v["name"] + "\n"
        string_representation += "env: " + str(self.v["env"]) + "\n"

        string_representation += "params: "
        for param in self.v["params"]:
            string_representation += str(param) + " "
        string_representation += "\n"

        string_representation += "body: "  + "\n"
        string_representation += str(self.v["body"]) + "\n"

        string_representation += "id: " + str(self.v["id"]) + "\n"

        string_representation += "END\n"

        return string_representation
    
    


    