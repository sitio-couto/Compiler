int test(int d, int e);
// float test(int d, int e);
// int test(int d, char e);
int test(int x, int y);

int sum() {
    return 1+1;
}

void test2(int l_id, int g_id , int const, int fcall, float biex, int unex);

int g_id = 100;

int main( ){
    int a=0, b=0;
    float f = 0.0;
    int c = 1;
    test2(c, g_id, 10, sum(), (0.3+0.1), ++b);
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
