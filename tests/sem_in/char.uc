int test(char c){
    return 1;
}

int main () {
    char c = 'c';
    int a = test(c);
    int b = test('c');
    return a;
}