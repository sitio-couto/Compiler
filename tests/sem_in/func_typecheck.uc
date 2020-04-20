int test(int d, int e);
// float test(int d, int e);
// int test(int d, char e);
int test(int x, int y);

int main( ){
    int a=0, b=0;
    float c=0.0;
    test(a, b);
    return 0;
}


int test(int a, int b) {
    return a + b;
}

// float test(int a, int b) {
//     return a + b;
// }

// int test(int a, char b) {
//     return a + b;
// }

// int test(int a, int b) {
//     return a*b;
// }
