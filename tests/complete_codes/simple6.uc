// Example 6:
    
int main() {
    int h, b;
    float area;
    read(h);
    read(b);
    /*
        Formula for the area of the triangle = (height x base)/2
        Also, typecasting denominator from int to float
    */
    area = (float)(h*b)/(float)2;
    print("The area of the triangle is: ", area);
    return 0;
}
