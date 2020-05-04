/* Bubble sort code */

int main() {
    int v[100];
    int n, c, d, swap;
    print("Enter number of elements: ");
    read(n);
    print("Enter ", n, " integers: ");
    for (c = 0; c < n; c++)
        read(v[c]);
    for (c = 0; c < n-1; c++)
        for (d = 0; d < n-c-1; d++)
            if (v[d] > v[d+1]) {
                swap = v[d];
                v[d] = v[d+1];
                v[d+1] = swap;
            }
    print("Sorted list in ascending order: ");
    for (c = 0; c < n; c++)
        print(v[c], " ");
    return 0;
}
