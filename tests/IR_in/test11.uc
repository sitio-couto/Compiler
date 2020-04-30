int main () {
    int x, y;
    int *r = &x;
    *r = y;
    x = *r;
    return 1;
}
