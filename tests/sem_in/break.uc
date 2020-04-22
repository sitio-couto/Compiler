int main (int a) {
    int i;
    int b = -1;

    for (i=0; i<10; ++i){
        i = i+1;
        break;
    }

    // break;

    while (b==-1) {
        for (i=0; i<10; ++i){
            i = i+1;
            break;
        }
        break;
    }
    
    i=0;
    // test('c', 0.0);

    return 0;
}
