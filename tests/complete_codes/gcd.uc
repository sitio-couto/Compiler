/* Compute GCD of two integers */

int gcd (int x, int y) {
    int g = y;
    while (x > 0) {
        g = x;
	    x = y - (y/x) * x;
	    y = g;
    }
    return g;
}

void main() {
    int a, b;
    print("give-me two integers separated by space:");
    read (a,b);
    print ("GCD of ", a, b, " is ", gcd(a,b));
    return;
}
