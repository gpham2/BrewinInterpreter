

from interpreterv4 import *

def main():
    # Create the interpreter
    interpreter = Interpreter(trace_output=False)


    program = """

   
        
func main() {
  a = @;
  a.f = lambda(x) { print(x); };
  a.f(10);
  a.f("foo");
}

    """


    program1 = """

   
        
func main() {
  a = @;
  a.x = 10;
  a.f = lambda(x) { this.x = x; };
	a.f(5);
  print(a.x);
}

    """

    program2 = """
func main() {
  a = @;
  a.f = lambda(x) { print(x); };
	a.f(10);
  a.f("foo");
}


"""

    program3 = """ 

func main() {
 c = @;
 c.y = 2;
 a = "string";
 print(a);
 print(1 && true);
 print(0 && true);
 /* d captures object c by object reference */ 
 d = lambda() { c.x = 5; };

 d();  
 print(c.x);  /* prints 5, since closure modified original object */
}
"""


    program5 = """
    func main() {
 c = lambda() { print(1); };

 /* d captures closure c by reference */
 d = lambda() { c = lambda() { print(2); }; };

 d();
 c();  /* prints 2, since c was captured by reference by d */
}"""



    program6 = """

func main() {
    a = 1;
    x = @;
    x.bar = lambda(y) {
        if (y < 10) {
            y = y + 1;
            x.bar(y);
        }
    };
    x.bar(a);
    print(a);
}


"""

    interpreter.run(program3)


if __name__ == '__main__':
    main()

