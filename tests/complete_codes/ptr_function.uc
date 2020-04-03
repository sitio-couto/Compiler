// The following program shows use of a function pointer
// for selecting between addition and subtraction:
    
int (*operation)(int x, int y);

int add(int x, int y) {
    return x + y;
}

int subtract(int x, int y) {
    return x - y;
}

int main() {
   int  foo = 1, bar = 1;
   operation = add;
   print(foo, " + ", bar, " = ", operation(foo, bar), "\n");
   operation = subtract;
   print(foo, " - ", bar, " = ", operation(foo, bar), "\n");
   return 0;
}
