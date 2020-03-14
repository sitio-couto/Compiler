// Example 5:
    
int main() {
    int var[] = {100, 200, 300};
    int *ptr;
    ptr = var;
    for(int i = 0; i < MAX; i++) {
        assert var[i] == *ptr;
        ptr++;
    }
    return 0;
}
