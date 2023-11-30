

from interpreterv3 import *

def main():
    # Create the interpreter
    interpreter = Interpreter(trace_output=True)


    program = """

   
        
func foo() { 
  print("hi");
}

func bar(a) {
  print(a);
}

func main() {
    b = 4;
  a = foo();
  d = bar(b);
  
}

    """


    program1 = """

   
        
func foo2(){
  return foo;
}

func foo(){
  print("hi");
}

func foo3() {
  return foo;
}
func main(){
  a = foo;
  b = a;
  print(a == foo);
}
    """

    program2 = """
func main() {
    i = 0;

    x = lambda(ref a, ref b) {
        a = a + 1;
        print(a);
        b = b + 1;
        print(b);

        y = lambda(ref c, ref d) {
            c = c + 1;
            print(c);
            d = d + 1;
            print(d);
        };

        y(a, b);
    };

    x(i, i);
    print(i);
}



""" # name error
    interpreter.run(program2)


if __name__ == '__main__':
    main()

