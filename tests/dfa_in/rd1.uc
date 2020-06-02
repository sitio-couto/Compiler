int main() {

  int a = 5;
  int c = 1;
  while (c < a) {
    c = c+c;
    print(c);
    print();
  }
  a = c-a;
  c = 0;

  return 0;
}
