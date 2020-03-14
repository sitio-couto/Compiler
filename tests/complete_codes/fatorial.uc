/* Compute the fatorial of an integer */

int fat (int n) {
    if (n == 0)
        return 1;
    else
        return n * fat (n-1);
}

void main() {
    assert fat(5) == 120;
    assert fat(6) == 720;
    assert fat(7) == 5040;
    return;
}
