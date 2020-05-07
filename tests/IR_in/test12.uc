

int (*operation)(int x, int y);

int add(int x, int y) {
    return x + y;
}

int subtract(int x, int y) {
    return x - y;
}

int main() {
   int  foo, bar;
   read(foo, bar);
   operation = &add;
   print(foo, " + ", bar, " = ", operation(foo, bar), ", ");
   operation = &subtract;
   print(foo, " - ", bar, " = ", operation(foo, bar));
   return 0;
}
