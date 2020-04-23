/* Display all prime numbers between two given interval: */

int main() {
    int n1, n2, i, j, flag;

    print("Enter 2 numbers (intervals) separated by space: ");
    read(n1, n2);
    print("Prime numbers between ", n1, " and ", n2, " are:\n");
    for (i = n1; i<= n2; i++) {
        flag = 1;
        for (j = 2; j <= i/2; j++)
            if (i % j == 0) {
                flag = 0;
                break;
            }
        if (flag == 1)
            print(i, "  ");
    }
    return 0;
}
