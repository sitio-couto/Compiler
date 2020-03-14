/* Check Armstrong Number: */

// Armstrong number is a number which is equal to sum of digits
// raise to the power total number of digits in the number. Ex:
// 0, 1, 2, 3, 153, 370, 407, 1634, 8208

int power (int n, int r) {
    int p = 1;
    for (int c = 1; c <= r; c++)
        p = p*n;
    return p;
}

int main() {
    int n, sum = 0;
    int temp, remainder, digits = 0;
    print("Input an integer: ");
    read(n);
    temp = n;
    while (temp != 0) {
        digits += 1;
        temp = temp / 10;
    }
    temp = n;
    while (temp != 0) {
        remainder = temp % 10;
        sum = sum + power(remainder, digits);
        temp = temp / 10;
    }
    if (n == sum)
      print(n, " is an Armstrong number.\n");
    else
      print(n, " is not an Armstrong number.\n");
    return;
}
